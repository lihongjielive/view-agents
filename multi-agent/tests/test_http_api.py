"""HTTP POST /v1/workflows、/v1/proposals。"""
from __future__ import annotations

from fastapi.testclient import TestClient

from multi_agent.api_server import app


def test_post_workflows_and_proposals():
    client = TestClient(app)
    w = client.post(
        "/v1/workflows",
        json={"order_id": "HX-1", "after_sale_id": "AS-9", "refund_amount": 20},
    )
    assert w.status_code == 200
    wf = w.json()["workflow_id"]
    p = client.post(
        "/v1/proposals",
        json={
            "workflow_id": wf,
            "tool": "refund.create",
            "order_id": "HX-1",
            "after_sale_id": "AS-9",
            "amount": 20,
        },
    )
    assert p.status_code == 200
    assert p.json()["allow"] is True