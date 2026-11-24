"""Slide 03: six production rules (T03_*)."""
from __future__ import annotations

from datetime import timedelta

import pytest

from multi_agent.domain import TaskStatus, ToolOpStatus, WorkflowStatus, make_business_key
from multi_agent.engine import SupervisorEngine
from multi_agent.gateway import Proposal, ToolGateway
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.proposals import submit_proposal
from multi_agent.store import Store, _iso, _utcnow


def _proposal(**kwargs) -> Proposal:
    base = dict(
        tenant="T1",
        tool="refund.create",
        order_id="ORD-991",
        after_sale_id="AS-77",
        amount=10.0,
        actor="agent-refund",
        approval_snapshot_id="appr-default",
    )
    base.update(kwargs)
    return Proposal(**base)


@pytest.fixture
def ctx():
    store = Store(":memory:")
    wf = store.create_workflow(
        tenant="T1",
        order_id="ORD-991",
        after_sale_id="AS-77",
        refund_amount=100.0,
    )
    gateway = ToolGateway(store)
    return store, wf, gateway


def test_T03_merge(ctx):
    store, wf, gateway = ctx
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    bk = refund.business_key or make_business_key("T1", "refund.create", "ORD-991", "AS-77")
    store.upsert_tool_operation_pending(
        business_key=bk, tool_name="refund.create", task_id=refund.id, payload={}
    )
    store.update_tool_operation(bk, ToolOpStatus.CONFIRMED, remote_ref="rf-1")
    d = submit_proposal(gateway, wf, _proposal()).decision
    assert d.code == "T03_MERGE"
    assert d.allow is True


def test_T03_fence(ctx):
    store, wf, ctx_gateway = ctx
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    a = store.claim_task(refund.id, "worker-A")
    assert a
    snap_a, att_a = a.row_version, a.attempt_no
    store.set_task_running(refund.id, "worker-A", att_a)
    past = _utcnow() - timedelta(seconds=60)
    store._conn.execute(
        "UPDATE tasks SET lease_until=?, status=? WHERE id=?",
        (_iso(past), TaskStatus.READY.value, refund.id),
    )
    store._conn.commit()
    b = store.claim_task(refund.id, "worker-B")
    assert b
    assert not store.fenced_task_update(
        task_id=refund.id,
        owner="worker-A",
        attempt_no=att_a,
        row_version=snap_a,
        to_status=TaskStatus.SUCCEEDED,
    )


def test_T03_dep(ctx):
    store, wf, gateway = ctx
    d = submit_proposal(
        gateway,
        wf,
        _proposal(tool="coupon.issue"),
    ).decision
    assert d.code == "T03_DEP"
    assert d.allow is False


def test_T03_comp(ctx):
    store, wf, gateway = ctx
    store.set_workflow_status(wf, WorkflowStatus.COMPENSATING)
    d = submit_proposal(gateway, wf, _proposal()).decision
    assert d.code == "T03_COMP"
    assert d.allow is False


def test_T03_trace():
    reset_state()
    pay = PaymentClient("asgi://payment")
    pay.set_fault("drop_response_after_success")
    store = Store(":memory:")
    engine = SupervisorEngine(store, pay)
    wf = engine.start_case()
    engine.run_refund_workflow(wf)
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    op = store.get_tool_operation(refund.business_key or "")
    assert op["status"] == ToolOpStatus.UNKNOWN.value
    pay.clear_fault()
    assert engine.reconcile_refund(wf)
    op2 = store.get_tool_operation(refund.business_key or "")
    assert op2["status"] == ToolOpStatus.CONFIRMED.value


def test_T03_audit(ctx):
    store, wf, gateway = ctx
    before = store.count_audit("gateway.evaluate")
    d = submit_proposal(gateway, wf, _proposal()).decision
    assert d.allow and d.code == "OK"
    after = store.count_audit("gateway.evaluate")
    assert after == before + 1
    row = store._conn.execute(
        "SELECT detail_json FROM audit_log WHERE action='gateway.evaluate' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row
    assert "T1:refund.create" in row["detail_json"]