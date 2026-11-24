"""Supervisor 编排入口（图 01）：建单、驱动 Worker、刷 Outbox。

非 LLM Supervisor：此处是确定性状态机编排；LLM 提议走 api_server / langgraph_poc。
"""
from __future__ import annotations

from multi_agent.gateway import ToolGateway
from multi_agent.outbox import OutboxPipeline
from multi_agent.payment.client import PaymentClient
from multi_agent.store import Store
from multi_agent.workers.coupon import CouponWorker
from multi_agent.workers.refund import RefundWorker


class SupervisorEngine:
    """组合 Store + Gateway + Workers + Outbox；每个 run_* 对应一张 docx 场景的演示切口。"""

    def __init__(self, store: Store, payment: PaymentClient) -> None:
        self.store = store
        self.payment = payment
        self.gateway = ToolGateway(store)
        self.outbox = OutboxPipeline(store)

    def start_case(
        self,
        *,
        tenant: str = "T1",
        order_id: str = "ORD-991",
        after_sale_id: str = "AS-77",
        refund_amount: float = 100.0,
    ) -> str:
        """创建 refund+coupon 工作流；返回 workflow_id。"""
        return self.store.create_workflow(
            tenant=tenant,
            order_id=order_id,
            after_sale_id=after_sale_id,
            refund_amount=refund_amount,
        )

    def run_refund_workflow(
        self, workflow_id: str, refund_amount: float = 100.0
    ) -> bool:
        """跑一次退款 Worker，并模拟 Kafka：发布 + 幂等消费 outbox。"""
        tasks = self.store.list_tasks(workflow_id)
        refund = next(t for t in tasks if t.logical_step_key == "refund")
        worker = RefundWorker(self.store, self.payment, self.gateway, "refund-worker-1")
        ok = worker.run_once(refund.id, refund_amount)
        self.outbox.publish_pending()
        self.outbox.ingest_all()
        return ok

    def reconcile_refund(self, workflow_id: str) -> bool:
        tasks = self.store.list_tasks(workflow_id)
        refund = next(t for t in tasks if t.logical_step_key == "refund")
        worker = RefundWorker(self.store, self.payment, self.gateway, "refund-worker-1")
        return worker.reconcile(refund.id)

    def run_reconciliation_batch(self, workflow_id: str) -> dict:
        """对账队列：按 business_key 调支付 Mock 批量对账（图 05/08）。"""
        keys: list[str] = []
        for t in self.store.list_tasks(workflow_id):
            if t.business_key:
                keys.append(t.business_key)
        if not keys:
            return {"found": [], "missing": []}
        return self.payment.reconciliation_by_keys(keys)

    def run_coupon(self, workflow_id: str, coupon_amount: float = 10.0) -> bool:
        tasks = self.store.list_tasks(workflow_id)
        coupon = next(t for t in tasks if t.logical_step_key == "coupon")
        worker = CouponWorker(self.store, self.gateway, "coupon-worker-1")
        return worker.run_once(coupon.id, coupon_amount)

    def run_full_happy_path(
        self,
        *,
        tenant: str = "T1",
        order_id: str = "ORD-991",
        after_sale_id: str = "AS-77",
        refund_amount: float = 100.0,
        coupon_amount: float = 10.0,
    ):
        """图 01 E2E 骨架入口；详情见 `e2e_skeleton.run_figure01_happy_path`."""
        from multi_agent.e2e_skeleton import run_figure01_happy_path

        return run_figure01_happy_path(
            self,
            tenant=tenant,
            order_id=order_id,
            after_sale_id=after_sale_id,
            refund_amount=refund_amount,
            coupon_amount=coupon_amount,
        )