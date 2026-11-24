"""图 10 — 监控指标。"""
from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from multi_agent.domain import TaskStatus, WorkflowStatus
from multi_agent.engine import SupervisorEngine
from multi_agent.metrics import (
    METRIC_KAFKA_CONSUMER_LAG,
    METRIC_READY_OLDEST_AGE,
    METRIC_READY_PENDING,
    METRIC_UNKNOWN_OPS,
    MetricsCollector,
)
from multi_agent.metrics_server import app
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.store import Store, _iso, _utcnow


@pytest.mark.metrics
def test_unknown_count_after_figure02_timeout():
    reset_state()
    store = Store(":memory:")
    engine = SupervisorEngine(store, PaymentClient("asgi://payment"))
    engine.payment.set_fault("drop_response_after_success")
    wf = engine.start_case()
    engine.run_refund_workflow(wf)

    m = MetricsCollector(store).collect()
    assert m[METRIC_UNKNOWN_OPS] >= 1.0
    assert m[METRIC_READY_PENDING] == 0.0


@pytest.mark.metrics
def test_ready_backlog_oldest_age():
    store = Store(":memory:")
    wf = store.create_workflow(
        tenant="T1", order_id="O", after_sale_id="A", refund_amount=1.0
    )
    past = _utcnow() - timedelta(minutes=5)
    store._conn.execute(
        "UPDATE tasks SET status=?, created_at=? WHERE workflow_id=? AND logical_step_key='coupon'",
        (TaskStatus.READY.value, _iso(past), wf),
    )
    store._conn.commit()

    m = MetricsCollector(store).collect()
    assert m[METRIC_READY_PENDING] >= 1.0
    assert m[METRIC_READY_OLDEST_AGE] >= 300.0


@pytest.mark.metrics
def test_kafka_lag_proxy_from_unpublished_outbox():
    store = Store(":memory:")
    store.create_workflow(tenant="T1", order_id="O2", after_sale_id="A2", refund_amount=1.0)
    assert store.count_unpublished_outbox() >= 1
    m = MetricsCollector(store).collect()
    assert m[METRIC_KAFKA_CONSUMER_LAG] >= 1.0


@pytest.mark.metrics
def test_metrics_http_endpoint():
    from multi_agent.metrics_server import set_collector

    store = Store(":memory:")
    store.create_workflow(tenant="T1", order_id="Ox", after_sale_id="Ax", refund_amount=1.0)
    set_collector(MetricsCollector(store))
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    assert METRIC_UNKNOWN_OPS in r.text
    assert "multi_agent_task_ready_pending_count" in r.text


@pytest.mark.metrics
def test_compensation_backlog_metric():
    store = Store(":memory:")
    wf = store.create_workflow(tenant="T1", order_id="Oc", after_sale_id="Ac", refund_amount=1.0)
    store.set_workflow_status(wf, WorkflowStatus.COMPENSATING)
    m = MetricsCollector(store).collect()
    assert m["multi_agent_compensation_workflow_count"] >= 1.0