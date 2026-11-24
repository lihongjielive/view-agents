"""E2E: Python state-machine sim + payment mock (slides 01–02, 08–09)."""
from __future__ import annotations

from multi_agent.domain import TaskStatus, ToolOpStatus
from multi_agent.engine import SupervisorEngine
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.store import Store


def _engine() -> tuple[Store, SupervisorEngine]:
    reset_state()
    store = Store(":memory:")
    return store, SupervisorEngine(store, PaymentClient("asgi://payment"))


def test_happy_path_refund_then_coupon():
    store, engine = _engine()
    wf = engine.start_case()
    assert engine.run_refund_workflow(wf)
    tasks = {t.logical_step_key: t for t in store.list_tasks(wf)}
    assert tasks["coupon"].status == TaskStatus.READY
    assert engine.run_coupon(wf)
    tasks = {t.logical_step_key: t.status for t in store.list_tasks(wf)}
    assert tasks["refund"] == TaskStatus.SUCCEEDED
    assert tasks["coupon"] == TaskStatus.SUCCEEDED
    assert store.count_http_posts_to_payment() == 1


def test_response_drop_unknown_reconcile_no_double_refund():
    reset_state()
    pay = PaymentClient("asgi://payment")
    pay.set_fault("drop_response_after_success")
    store = Store(":memory:")
    engine = SupervisorEngine(store, pay)
    wf = engine.start_case()
    assert not engine.run_refund_workflow(wf)
    assert store.count_http_posts_to_payment() == 1
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    coupon = next(t for t in store.list_tasks(wf) if t.logical_step_key == "coupon")
    assert refund.status == TaskStatus.UNKNOWN
    assert coupon.status == TaskStatus.WAITING
    op = store.get_tool_operation(refund.business_key or "")
    assert op and op["status"] == ToolOpStatus.UNKNOWN.value
    pay.clear_fault()
    assert engine.reconcile_refund(wf)
    assert store.count_http_posts_to_payment() == 1
    assert engine.run_coupon(wf)


def test_business_key_idempotent_on_gateway():
    reset_state()
    pay = PaymentClient("asgi://payment")
    store = Store(":memory:")
    engine = SupervisorEngine(store, pay)
    wf = engine.start_case()
    engine.run_refund_workflow(wf)
    pay.set_fault("none")
    engine.run_refund_workflow(wf)
    assert store.count_http_posts_to_payment() == 1


def test_coupon_blocked_when_refund_unknown():
    store, engine = _engine()
    wf = engine.start_case()
    pay = engine.payment
    pay.set_fault("drop_response_after_success")
    engine.run_refund_workflow(wf)
    coupon = next(t for t in store.list_tasks(wf) if t.logical_step_key == "coupon")
    assert coupon.status == TaskStatus.WAITING
    assert not engine.run_coupon(wf)