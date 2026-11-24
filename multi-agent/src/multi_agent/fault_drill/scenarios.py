"""图 11 故障演练五场景（scripts/fault_drill/run_all.py 入口）。

覆盖：outbox ack 丢失、offset 前崩溃、租约过期栅栏、支付响应丢失、滞后回调。
"""
from __future__ import annotations

import time
from datetime import timedelta

from fastapi.testclient import TestClient

from multi_agent.domain import TaskStatus, ToolOpStatus, WorkflowStatus
from multi_agent.engine import SupervisorEngine
from multi_agent.outbox import OutboxPipeline
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import app, reset_state
from multi_agent.store import Store, _iso, _utcnow


def run_lost_publish_ack(store: Store | None = None) -> dict:
    """发布确认丢失 → 重发后事件仍唯一。"""
    store = store or Store(":memory:")
    store.create_workflow(tenant="T1", order_id="O1", after_sale_id="A1", refund_amount=1.0)
    pipeline = OutboxPipeline(store)
    assert store.count_unpublished_outbox() >= 1
    pipeline.publish_pending(simulate_ack_loss=True)
    assert store.count_unpublished_outbox() >= 1
    pipeline.publish_pending(simulate_ack_loss=False)
    assert store.count_unpublished_outbox() == 0
    return {"unpublished_after_retry": 0}


def run_crash_before_offset(store: Store | None = None) -> dict:
    """Offset 前崩溃 → 重放消费幂等。"""
    store = store or Store(":memory:")
    wf = store.create_workflow(tenant="T1", order_id="O2", after_sale_id="A2", refund_amount=1.0)
    pipeline = OutboxPipeline(store)
    pipeline.publish_pending()
    first = pipeline.ingest_all()
    second = pipeline.ingest_all()
    assert second == 0
    return {"workflow_id": wf, "first_ingest": first, "replay_ingest": second}


def run_worker_disconnect(store: Store | None = None) -> dict:
    """Worker A 失联 → B 接管；A 晚到 fenced 拒绝。"""
    store = store or Store(":memory:")
    wf = store.create_workflow(tenant="T1", order_id="O3", after_sale_id="A3", refund_amount=1.0)
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    a = store.claim_task(refund.id, "worker-A")
    assert a
    snap_a, att_a = a.row_version, a.attempt_no
    store.set_task_running(refund.id, "worker-A", att_a)
    past = _utcnow() - timedelta(seconds=120)
    store._conn.execute(
        "UPDATE tasks SET lease_until=?, status=? WHERE id=?",
        (_iso(past), TaskStatus.READY.value, refund.id),
    )
    store._conn.commit()
    b = store.claim_task(refund.id, "worker-B")
    assert b and b.attempt_no == att_a + 1
    rejected = store.fenced_task_update(
        task_id=refund.id,
        owner="worker-A",
        attempt_no=att_a,
        row_version=snap_a,
        to_status=TaskStatus.SUCCEEDED,
    )
    store.set_task_running(refund.id, "worker-B", b.attempt_no)
    accepted = store.fenced_task_update(
        task_id=refund.id,
        owner="worker-B",
        attempt_no=b.attempt_no,
        row_version=b.row_version,
        to_status=TaskStatus.SUCCEEDED,
        bump_result=True,
    )
    assert not rejected and accepted
    return {"worker_b_attempt": b.attempt_no}


def run_success_response_lost(store: Store | None = None) -> dict:
    """成功响应丢失 → UNKNOWN → 查询收敛，无第二笔 POST。"""
    reset_state()
    pay = PaymentClient("asgi://payment")
    pay.set_fault("drop_response_after_success")
    store = store or Store(":memory:")
    engine = SupervisorEngine(store, pay)
    wf = engine.start_case(tenant="T1", order_id="O4", after_sale_id="A4")
    assert not engine.run_refund_workflow(wf)
    assert store.count_http_posts_to_payment() == 1
    pay.clear_fault()
    assert engine.reconcile_refund(wf)
    assert store.count_http_posts_to_payment() == 1
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    assert refund.status == TaskStatus.SUCCEEDED
    return {"posts": 1}


def run_late_callback() -> dict:
    """迟到回调：POST 504 但稍后 callbacks 有记录且 GET 可查。"""
    reset_state()
    c = TestClient(app)
    c.post(
        "/v1/admin/fault-injection",
        json={
            "mode": "late_callback",
            "scope": "global",
            "late_callback_delay_ms": 80,
        },
    )
    key = "T1:refund.create:O5:A5"
    r = c.post(
        "/v1/refunds",
        json={"business_key": key, "order_id": "O5", "after_sale_id": "A5", "amount": 5},
        headers={"X-Tenant": "T1"},
    )
    assert r.status_code == 504
    time.sleep(0.2)
    got = c.get(f"/v1/refunds/{key}")
    assert got.status_code == 200
    assert got.json()["state"] == "SUCCEEDED"
    callbacks = c.get("/v1/admin/callbacks").json()
    assert any(cb["business_key"] == key for cb in callbacks)
    c.delete("/v1/admin/fault-injection")
    return {"callback_count": len(callbacks)}