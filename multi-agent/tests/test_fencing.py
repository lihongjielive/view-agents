"""Slide 07: lease + fencing."""
from __future__ import annotations

from datetime import timedelta

from multi_agent.domain import TaskStatus
from multi_agent.store import Store, _utcnow, _iso


def test_old_worker_fenced_update_rejected():
    store = Store(":memory:")
    wf = store.create_workflow(
        tenant="T1", order_id="O1", after_sale_id="A1", refund_amount=1.0
    )
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")

    a = store.claim_task(refund.id, "worker-A")
    assert a
    snap_a = a.row_version
    attempt_a = a.attempt_no
    store.set_task_running(refund.id, "worker-A", attempt_a)

    past = _utcnow() - timedelta(seconds=60)
    store._conn.execute(
        "UPDATE tasks SET lease_until=?, owner=NULL WHERE id=?",
        (_iso(past), refund.id),
    )
    store._conn.commit()
    store._conn.execute(
        "UPDATE tasks SET status=? WHERE id=?",
        (TaskStatus.READY.value, refund.id),
    )
    store._conn.commit()

    b = store.claim_task(refund.id, "worker-B")
    assert b and b.attempt_no == attempt_a + 1

    ok_a = store.fenced_task_update(
        task_id=refund.id,
        owner="worker-A",
        attempt_no=attempt_a,
        row_version=snap_a,
        to_status=TaskStatus.SUCCEEDED,
    )
    assert not ok_a

    store.set_task_running(refund.id, "worker-B", b.attempt_no)
    ok_b = store.fenced_task_update(
        task_id=refund.id,
        owner="worker-B",
        attempt_no=b.attempt_no,
        row_version=b.row_version,
        to_status=TaskStatus.SUCCEEDED,
        bump_result=True,
    )
    assert ok_b