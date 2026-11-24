"""图 04 — business_key。"""
from __future__ import annotations

import pytest

from multi_agent.domain import make_business_key, parse_business_key
from multi_agent.engine import SupervisorEngine
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.store import Store


@pytest.mark.figure04
def test_business_key_format():
    k = make_business_key("T1", "refund.create", "ORD-1", "AS-1")
    p = parse_business_key(k)
    assert p.tenant == "T1"
    assert p.tool == "refund.create"


@pytest.mark.figure04
def test_attempt_unchanged_key_stable_on_retry():
    reset_state()
    store = Store(":memory:")
    engine = SupervisorEngine(store, PaymentClient("asgi://payment"))
    wf = engine.start_case()
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    k1 = refund.business_key
    engine.run_refund_workflow(wf)
    refund2 = store.get_task(refund.id)
    assert refund2 and refund2.business_key == k1
    assert refund2.attempt_no >= 1