"""图 08 — NEEDS_REVIEW + 禁止盲重试 POST。"""
from __future__ import annotations

import pytest

from multi_agent.domain import TaskStatus, WorkflowStatus
from multi_agent.engine import SupervisorEngine
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.store import Store


@pytest.mark.figure08
def test_needs_review_when_remote_missing():
    reset_state()
    pay = PaymentClient("asgi://payment")
    pay.set_fault("drop_response_after_success")
    store = Store(":memory:")
    engine = SupervisorEngine(store, pay)
    wf = engine.start_case()
    engine.run_refund_workflow(wf)
    assert store.count_http_posts_to_payment() == 1
    reset_state()  # 模拟远端不可查
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    assert not engine.reconcile_refund(wf)
    assert store.get_workflow_status(wf) == WorkflowStatus.NEEDS_REVIEW
    assert store.reconciliation_open_count(wf) >= 1
    engine.run_refund_workflow(wf)
    assert store.count_http_posts_to_payment() == 1


@pytest.mark.figure08
def test_pending_before_post_order():
    reset_state()
    store = Store(":memory:")
    engine = SupervisorEngine(store, PaymentClient("asgi://payment"))
    wf = engine.start_case()
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    task = store.claim_task(refund.id, "w1")
    assert task
    store.set_task_running(refund.id, "w1", task.attempt_no)
    store.upsert_tool_operation_pending(
        business_key=refund.business_key or "",
        tool_name="refund.create",
        task_id=refund.id,
        payload={"amount": 1.0},
    )
    assert store.get_tool_operation(refund.business_key or "")
    assert store.count_http_posts_to_payment() == 0