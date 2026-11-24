"""Refund worker — persist, call payment, UNKNOWN + reconcile (slide 08)."""
from __future__ import annotations

from multi_agent.domain import TaskStatus, ToolOpStatus, WorkflowStatus, parse_business_key
from multi_agent.gateway import Proposal, ToolGateway
from multi_agent.payment.client import PaymentClient
from multi_agent.store import Store


class RefundWorker:
    """图 02/08：claim → Gateway → tool_op → 支付 POST；超时进 UNKNOWN，reconcile 只 GET。"""

    def __init__(
        self,
        store: Store,
        payment: PaymentClient,
        gateway: ToolGateway,
        worker_id: str,
    ) -> None:
        self.store = store
        self.payment = payment
        self.gateway = gateway
        self.worker_id = worker_id

    def run_once(self, task_id: str, amount: float) -> bool:
        # 1) 租约认领  2) Gateway（含 T03_MERGE）  3) 幂等已确认则直接成功
        # 4) PENDING + audit payment.post_refund  5) 支付调用 → CONFIRMED/UNKNOWN/FAILED
        task = self.store.claim_task(task_id, self.worker_id)
        if not task or not task.business_key:
            return False
        if self.store.get_workflow_status(task.workflow_id) == WorkflowStatus.NEEDS_REVIEW:
            return False
        parts = parse_business_key(task.business_key)
        decision = self.gateway.evaluate(
            task.workflow_id,
            Proposal(
                tenant=parts.tenant,
                tool=parts.tool,
                order_id=parts.order_id,
                after_sale_id=parts.after_sale_id,
                amount=amount,
                actor=self.worker_id,
                approval_snapshot_id="appr-default",
            ),
        )
        if not decision.allow and decision.code != "T03_MERGE":
            self.store.fenced_task_update(
                task_id=task.id,
                owner=self.worker_id,
                attempt_no=task.attempt_no,
                row_version=task.row_version,
                to_status=TaskStatus.FAILED,
            )
            return False

        snap = task.row_version
        attempt = task.attempt_no
        self.store.set_task_running(task.id, self.worker_id, attempt)

        prior = self.store.get_tool_operation(task.business_key)
        if prior and prior["status"] == ToolOpStatus.CONFIRMED.value:
            ok = self.store.fenced_task_update(
                task_id=task.id,
                owner=self.worker_id,
                attempt_no=attempt,
                row_version=snap,
                to_status=TaskStatus.SUCCEEDED,
                bump_result=True,
            )
            self.store.try_promote_coupon_after_refund(task.workflow_id)
            return ok

        self.store.upsert_tool_operation_pending(
            business_key=task.business_key,
            tool_name="refund.create",
            task_id=task.id,
            payload={"amount": amount},
        )
        self.store.audit(
            self.worker_id,
            "payment.post_refund",
            {"business_key": task.business_key},
        )

        kind, body, _ = self.payment.post_refund(
            tenant=parts.tenant,
            business_key=task.business_key,
            order_id=parts.order_id,
            after_sale_id=parts.after_sale_id,
            amount=amount,
        )

        if kind == "ok" and body:
            self.store.update_tool_operation(
                task.business_key,
                ToolOpStatus.CONFIRMED,
                remote_ref=body.get("refund_id"),
            )
            ok = self.store.fenced_task_update(
                task_id=task.id,
                owner=self.worker_id,
                attempt_no=attempt,
                row_version=snap,
                to_status=TaskStatus.SUCCEEDED,
                bump_result=True,
            )
            self.store.try_promote_coupon_after_refund(task.workflow_id)
            return ok

        if kind == "timeout":
            self.store.update_tool_operation(task.business_key, ToolOpStatus.UNKNOWN)
            self.store.fenced_task_update(
                task_id=task.id,
                owner=self.worker_id,
                attempt_no=attempt,
                row_version=snap,
                to_status=TaskStatus.UNKNOWN,
            )
            return False

        self.store.update_tool_operation(task.business_key, ToolOpStatus.FAILED)
        self.store.fenced_task_update(
            task_id=task.id,
            owner=self.worker_id,
            attempt_no=attempt,
            row_version=snap,
            to_status=TaskStatus.FAILED,
        )
        return False

    def reconcile(self, task_id: str) -> bool:
        """Query remote by business_key (slide 08). No blind POST."""
        task = self.store.get_task(task_id)
        if not task or task.status != TaskStatus.UNKNOWN or not task.business_key:
            return False
        remote = self.payment.get_refund(task.business_key)
        if not remote:
            self.store.escalate_needs_review(
                task.workflow_id,
                task_id=task.id,
                reason="remote_not_found",
                business_key=task.business_key,
            )
            return False
        if remote.get("state") == "SUCCEEDED":
            self.store.update_tool_operation(
                task.business_key,
                ToolOpStatus.CONFIRMED,
                remote_ref=remote.get("refund_id"),
            )
            self.store._conn.execute(
                """
                UPDATE tasks SET status=?, row_version=row_version+1,
                    result_version=result_version+1, owner=NULL, lease_until=NULL
                WHERE id=? AND status='UNKNOWN'
                """,
                (TaskStatus.SUCCEEDED.value, task_id),
            )
            self.store._conn.commit()
            self.store.try_promote_coupon_after_refund(task.workflow_id)
            return True
        return False