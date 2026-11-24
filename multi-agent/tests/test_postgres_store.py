"""P2：PostgreSQL Store（需 MULTI_AGENT_POSTGRES_DSN）。"""
from __future__ import annotations

import os

import pytest

from multi_agent.domain import TaskStatus
from multi_agent.engine import SupervisorEngine
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.store_factory import open_store

pytestmark = pytest.mark.postgres


def test_open_store_sqlite_memory():
    store = open_store("sqlite::memory:")
    wf = store.create_workflow(
        tenant="T",
        order_id="O",
        after_sale_id="A",
        refund_amount=1.0,
    )
    tasks = store.list_tasks(wf)
    assert len(tasks) == 2


def test_postgres_create_workflow_and_engine():
    psycopg = pytest.importorskip("psycopg")
    _ = psycopg
    dsn = os.environ.get("MULTI_AGENT_POSTGRES_DSN")
    if not dsn:
        pytest.skip("MULTI_AGENT_POSTGRES_DSN not set")
    reset_state()
    store = open_store(dsn)
    payment = PaymentClient("asgi://payment")
    engine = SupervisorEngine(store, payment)
    wf = engine.start_case(
        tenant="T1",
        order_id="PG-1",
        after_sale_id="AS-1",
        refund_amount=2.0,
    )
    assert engine.run_refund_workflow(wf, refund_amount=2.0)
    assert engine.run_coupon(wf, coupon_amount=1.0)
    tasks = {t.logical_step_key: t.status for t in store.list_tasks(wf)}
    assert tasks["refund"] == TaskStatus.SUCCEEDED
    assert tasks["coupon"] == TaskStatus.SUCCEEDED