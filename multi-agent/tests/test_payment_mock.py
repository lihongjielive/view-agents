"""Payment gateway mock API coverage."""
from __future__ import annotations

from fastapi.testclient import TestClient

from multi_agent.payment.server import app, reset_state


def test_idempotent_refund_post():
    reset_state()
    c = TestClient(app)
    body = {
        "business_key": "T1:refund.create:O1:A1",
        "order_id": "O1",
        "after_sale_id": "A1",
        "amount": 9.9,
    }
    r1 = c.post("/v1/refunds", json=body, headers={"X-Tenant": "T1"})
    r2 = c.post("/v1/refunds", json=body, headers={"X-Tenant": "T1"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["idempotent_hit"] is True
    metrics = c.get("/v1/admin/metrics").json()
    assert metrics["post_attempts"][body["business_key"]] == 2
    assert c.get(f"/v1/refunds/{body['business_key']}").json()["state"] == "SUCCEEDED"


def test_drop_response_after_success():
    reset_state()
    c = TestClient(app)
    c.post(
        "/v1/admin/fault-injection",
        json={"mode": "drop_response_after_success", "scope": "global"},
    )
    body = {
        "business_key": "T1:refund.create:O2:A2",
        "order_id": "O2",
        "after_sale_id": "A2",
        "amount": 1.0,
    }
    r = c.post("/v1/refunds", json=body, headers={"X-Tenant": "T1"})
    assert r.status_code == 504
    got = c.get(f"/v1/refunds/{body['business_key']}").json()
    assert got["state"] == "SUCCEEDED"


def test_reconciliation_batch():
    reset_state()
    c = TestClient(app)
    key = "T1:refund.create:O3:A3"
    c.post(
        "/v1/refunds",
        json={
            "business_key": key,
            "order_id": "O3",
            "after_sale_id": "A3",
            "amount": 3.0,
        },
        headers={"X-Tenant": "T1"},
    )
    rep = c.post("/v1/reconciliation/by-keys", json=[key, "missing"])
    assert len(rep.json()["found"]) == 1
    assert rep.json()["missing"] == ["missing"]