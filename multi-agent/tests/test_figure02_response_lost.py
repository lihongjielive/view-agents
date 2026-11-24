"""图 02 — 矩阵 §02 验收。"""
from __future__ import annotations

import pytest

from multi_agent.domain import TaskStatus, ToolOpStatus
from multi_agent.e2e_figure02 import run_figure02_response_lost
from multi_agent.engine import SupervisorEngine
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.store import Store


@pytest.fixture
def engine():
    reset_state()
    store = Store(":memory:")
    return SupervisorEngine(store, PaymentClient("asgi://payment"))


@pytest.mark.figure02
def test_figure02_timeout_not_failure(engine):
    result = run_figure02_response_lost(engine)
    assert result.refund_status == TaskStatus.SUCCEEDED
    assert result.coupon_status == TaskStatus.SUCCEEDED
    assert result.payment_post_count == 1
    assert result.after_reconcile


@pytest.mark.figure02
def test_figure02_matrix_coupon_waiting_until_reconcile(engine):
    engine.payment.set_fault("drop_response_after_success")
    wf = engine.start_case()
    engine.run_refund_workflow(wf)
    coupon = next(t for t in engine.store.list_tasks(wf) if t.logical_step_key == "coupon")
    refund = next(t for t in engine.store.list_tasks(wf) if t.logical_step_key == "refund")
    assert refund.status == TaskStatus.UNKNOWN
    assert refund.status != TaskStatus.FAILED
    assert coupon.status == TaskStatus.WAITING
    op = engine.store.get_tool_operation(refund.business_key or "")
    assert op["status"] == ToolOpStatus.UNKNOWN.value
    assert engine.store.count_http_posts_to_payment() == 1