"""图 02 — 网关已成功、Agent 只见超时（超时 ≠ 失败）。"""
from __future__ import annotations

from dataclasses import dataclass

from multi_agent.domain import TaskStatus, ToolOpStatus
from multi_agent.engine import SupervisorEngine


@dataclass(frozen=True)
class Figure02Result:
    workflow_id: str
    refund_status: TaskStatus
    coupon_status: TaskStatus
    tool_op_status: str
    payment_post_count: int
    after_reconcile: bool


def run_figure02_response_lost(
    engine: SupervisorEngine,
    *,
    refund_amount: float = 100.0,
    coupon_amount: float = 10.0,
) -> Figure02Result:
    """响应丢失 → UNKNOWN → 查询收敛；全程最多一笔 POST。"""
    engine.payment.set_fault("drop_response_after_success")
    wf = engine.start_case()
    engine.run_refund_workflow(wf, refund_amount=refund_amount)

    tasks = {t.logical_step_key: t for t in engine.store.list_tasks(wf)}
    refund = tasks["refund"]
    coupon = tasks["coupon"]
    op = engine.store.get_tool_operation(refund.business_key or "")
    posts_after_timeout = engine.store.count_http_posts_to_payment()

    assert refund.status == TaskStatus.UNKNOWN, "超时不得标 FAILED"
    assert refund.status != TaskStatus.FAILED
    assert coupon.status == TaskStatus.WAITING
    assert op and op["status"] == ToolOpStatus.UNKNOWN.value
    assert posts_after_timeout == 1

    engine.payment.clear_fault()
    reconciled = engine.reconcile_refund(wf)
    assert engine.store.count_http_posts_to_payment() == 1

    if reconciled:
        engine.run_coupon(wf, coupon_amount=coupon_amount)

    tasks2 = {t.logical_step_key: t for t in engine.store.list_tasks(wf)}
    op2 = engine.store.get_tool_operation(refund.business_key or "")
    return Figure02Result(
        workflow_id=wf,
        refund_status=tasks2["refund"].status,
        coupon_status=tasks2["coupon"].status,
        tool_op_status=(op2 or op)["status"],
        payment_post_count=engine.store.count_http_posts_to_payment(),
        after_reconcile=reconciled,
    )