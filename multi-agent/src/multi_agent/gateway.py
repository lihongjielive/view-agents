"""Tool Gateway：模型/Worker 只能提议，系统裁决是否允许写（图 03、09）。

规则摘要（对应 audit code）：
- MERGE：相同 business_key 已有进行中的退款 → allow（幂等合并）
- FENCE：NEEDS_REVIEW / 补偿窗口禁止新写
- DEP：发券依赖退款 SUCCEEDED
- COMP：approval_snapshot / tenant 校验
- 额度：TENANT_QUOTA
- TRACE：每次 evaluate 写 audit_log
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from multi_agent.domain import WorkflowStatus, make_business_key
from multi_agent.store import Store

# 租户额度（配置驱动，spec GW-4）
TENANT_QUOTA: dict[str, dict[str, float]] = {
    "T1": {"refund_max": 50_000.0, "coupon_max": 500.0},
}


@dataclass
class GatewayDecision:
    allow: bool
    reason: str
    code: str


@dataclass
class Proposal:
    tenant: str
    tool: str
    order_id: str
    after_sale_id: str
    amount: float
    actor: str
    approval_snapshot_id: str
    access_token: str = "token-valid"


class ToolGateway:
    """只读 Store + 写 audit；不调用支付、不直接改 Task 状态。"""

    def __init__(self, store: Store) -> None:
        self.store = store

    def evaluate(self, workflow_id: str, proposal: Proposal) -> GatewayDecision:
        """按序过门禁；返回 allow/code/reason 供 Proposal 层与 Worker 分支。"""
        wf_row = self.store._conn.execute(
            "SELECT * FROM workflows WHERE id=?", (workflow_id,)
        ).fetchone()
        if not wf_row:
            d = GatewayDecision(False, "workflow_not_found", "WF404")
            self._audit(proposal, workflow_id, None, d)
            return d

        status = WorkflowStatus(wf_row["status"])
        if status == WorkflowStatus.NEEDS_REVIEW:
            d = GatewayDecision(False, "workflow_needs_review", "T03_REVIEW")
            self._audit(proposal, workflow_id, None, d)
            return d

        if status == WorkflowStatus.COMPENSATING:
            d = GatewayDecision(False, "compensation_window_no_new_writes", "T03_COMP")
            self._audit(proposal, workflow_id, None, d)
            return d

        if proposal.access_token != "token-valid":
            d = GatewayDecision(False, "token_invalid", "T09_TOKEN")
            self._audit(proposal, workflow_id, None, d)
            return d

        if wf_row["approval_snapshot_id"] != proposal.approval_snapshot_id:
            d = GatewayDecision(False, "approval_snapshot_invalid", "T03_APPROVAL")
            self._audit(proposal, workflow_id, None, d)
            return d

        if proposal.tenant != wf_row["tenant"]:
            d = GatewayDecision(False, "tenant_mismatch", "T03_TENANT")
            self._audit(proposal, workflow_id, None, d)
            return d

        quota = TENANT_QUOTA.get(proposal.tenant, {})
        cap_key = "refund_max" if proposal.tool == "refund.create" else "coupon_max"
        cap = quota.get(cap_key)
        if cap is not None and proposal.amount > cap:
            d = GatewayDecision(False, "quota_exceeded", "T03_QUOTA")
            self._audit(proposal, workflow_id, None, d)
            return d

        if proposal.amount <= 0:
            d = GatewayDecision(False, "amount_invalid", "T03_FACT")
            self._audit(proposal, workflow_id, None, d)
            return d

        bk = make_business_key(
            proposal.tenant, proposal.tool, proposal.order_id, proposal.after_sale_id
        )
        if proposal.tool == "refund.create":
            existing = self.store.get_tool_operation(bk)
            if existing and existing["status"] in ("PENDING", "UNKNOWN", "CONFIRMED"):
                d = GatewayDecision(
                    True,
                    "business_key_merge_existing",
                    "T03_MERGE",
                )
                self._audit(proposal, workflow_id, bk, d)
                return d

        if proposal.tool == "coupon.issue":
            tasks = {
                t.logical_step_key: t
                for t in self.store.list_tasks(workflow_id)
            }
            refund = tasks.get("refund")
            if not refund or refund.status.value != "SUCCEEDED":
                d = GatewayDecision(False, "dependency_refund_not_done", "T03_DEP")
                self._audit(proposal, workflow_id, bk, d)
                return d

        d = GatewayDecision(True, "allowed", "OK")
        self._audit(proposal, workflow_id, bk, d)
        return d

    def _audit(
        self,
        proposal: Proposal,
        workflow_id: str,
        business_key: str | None,
        decision: GatewayDecision,
    ) -> None:
        detail: dict[str, Any] = {
            "workflow_id": workflow_id,
            "tool": proposal.tool,
            "business_key": business_key,
            "allow": decision.allow,
            "code": decision.code,
            "reason": decision.reason,
        }
        self.store.audit(proposal.actor, "gateway.evaluate", detail)