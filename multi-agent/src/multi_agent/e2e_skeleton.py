"""图 01 可恢复协议 — 一键 E2E 骨架（Supervisor → Workers → Payment）。"""
from __future__ import annotations

from dataclasses import dataclass

from multi_agent.domain import TaskStatus, WorkflowStatus
from multi_agent.engine import SupervisorEngine


@dataclass(frozen=True)
class Figure01Result:
    workflow_id: str
    refund_status: TaskStatus
    coupon_status: TaskStatus
    workflow_status: WorkflowStatus
    payment_post_count: int
    refund_succeeded: bool
    coupon_succeeded: bool


def run_figure01_happy_path(
    engine: SupervisorEngine,
    *,
    tenant: str = "T1",
    order_id: str = "ORD-991",
    after_sale_id: str = "AS-77",
    refund_amount: float = 100.0,
    coupon_amount: float = 10.0,
) -> Figure01Result:
    """
    图 01 主路径：Supervisor 建单 → Refund Worker → DAG 放开发券 → Coupon Worker。
    """
    wf = engine.start_case(
        tenant=tenant,
        order_id=order_id,
        after_sale_id=after_sale_id,
        refund_amount=refund_amount,
    )
    tasks0 = {t.logical_step_key: t for t in engine.store.list_tasks(wf)}
    assert tasks0["refund"].status == TaskStatus.READY
    assert tasks0["coupon"].status == TaskStatus.WAITING

    refund_ok = engine.run_refund_workflow(wf, refund_amount=refund_amount)
    tasks1 = {t.logical_step_key: t for t in engine.store.list_tasks(wf)}
    assert tasks1["coupon"].status == TaskStatus.READY, "DAG 门：退款成功后发券 READY"

    coupon_ok = engine.run_coupon(wf, coupon_amount=coupon_amount)
    tasks2 = {t.logical_step_key: t for t in engine.store.list_tasks(wf)}
    return Figure01Result(
        workflow_id=wf,
        refund_status=tasks2["refund"].status,
        coupon_status=tasks2["coupon"].status,
        workflow_status=engine.store.get_workflow_status(wf),
        payment_post_count=engine.store.count_http_posts_to_payment(),
        refund_succeeded=refund_ok,
        coupon_succeeded=coupon_ok,
    )