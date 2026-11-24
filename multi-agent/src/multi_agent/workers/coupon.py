"""Coupon worker — issues coupon after DAG + gateway gates."""
from __future__ import annotations

from multi_agent.domain import TaskStatus, ToolOpStatus, parse_business_key
from multi_agent.gateway import Proposal, ToolGateway
from multi_agent.store import Store


class CouponWorker:
    """图 09：仅在 DAG READY 且 Gateway DEP 通过后执行；仿真发券无外部 HTTP。"""

    def __init__(self, store: Store, gateway: ToolGateway, worker_id: str) -> None:
        self.store = store
        self.gateway = gateway
        self.worker_id = worker_id

    def run_once(self, task_id: str, coupon_amount: float) -> bool:
        task = self.store.claim_task(task_id, self.worker_id)
        if not task or not task.business_key:
            return False
        parts = parse_business_key(task.business_key)
        decision = self.gateway.evaluate(
            task.workflow_id,
            Proposal(
                tenant=parts.tenant,
                tool=parts.tool,
                order_id=parts.order_id,
                after_sale_id=parts.after_sale_id,
                amount=coupon_amount,
                actor=self.worker_id,
                approval_snapshot_id="appr-default",
            ),
        )
        if not decision.allow:
            return False

        snap = task.row_version
        attempt = task.attempt_no
        self.store.set_task_running(task.id, self.worker_id, attempt)
        self.store.upsert_tool_operation_pending(
            business_key=task.business_key,
            tool_name="coupon.issue",
            task_id=task.id,
            payload={"coupon_amount": coupon_amount},
        )
        self.store.update_tool_operation(
            task.business_key, ToolOpStatus.CONFIRMED, remote_ref="cpn-sim"
        )
        return self.store.fenced_task_update(
            task_id=task.id,
            owner=self.worker_id,
            attempt_no=attempt,
            row_version=snap,
            to_status=TaskStatus.SUCCEEDED,
            bump_result=True,
        )