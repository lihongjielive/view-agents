"""P2：LangGraph 提议层 + multi_agent 执行。"""
from __future__ import annotations

import pytest

langgraph = pytest.importorskip("langgraph")

from multi_agent.domain import TaskStatus
from multi_agent.engine import SupervisorEngine
from multi_agent.langgraph_poc.graph import build_proposal_graph, run_poc_case
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.store import Store


@pytest.mark.langgraph_poc
def test_langgraph_poc_happy_path():
    out = run_poc_case()
    assert out.get("workflow_id")
    assert out.get("refund_proposal_code") == "OK"
    assert out.get("coupon_proposal_code") == "OK"
    assert out.get("refund_executed") is True
    assert out.get("coupon_executed") is True


@pytest.mark.langgraph_poc
def test_langgraph_propose_before_execute_no_direct_payment():
    reset_state()
    store = Store(":memory:")
    payment = PaymentClient("asgi://payment")
    engine = SupervisorEngine(store, payment)
    graph = build_proposal_graph(engine)
    initial = {
        "tenant": "T1",
        "order_id": "O",
        "after_sale_id": "A",
        "refund_amount": 10.0,
        "coupon_amount": 5.0,
    }
    for event in graph.stream(initial):
        if "propose_refund" in event:
            break
    assert store.count_http_posts_to_payment() == 0
    assert store.count_audit("gateway.evaluate") >= 1


@pytest.mark.langgraph_poc
def test_langgraph_poc_tasks_succeeded_in_store():
    reset_state()
    store = Store(":memory:")
    payment = PaymentClient("asgi://payment")
    engine = SupervisorEngine(store, payment)
    out = build_proposal_graph(engine).invoke(
        {
            "tenant": "T1",
            "order_id": "O2",
            "after_sale_id": "A2",
            "refund_amount": 1.0,
            "coupon_amount": 1.0,
        }
    )
    tasks = {t.logical_step_key: t.status for t in store.list_tasks(out["workflow_id"])}
    assert tasks["refund"] == TaskStatus.SUCCEEDED
    assert tasks["coupon"] == TaskStatus.SUCCEEDED