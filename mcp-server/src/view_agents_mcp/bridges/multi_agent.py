"""可选 HTTP 桥接：仅 workflow + proposal（禁止支付写）。"""
from __future__ import annotations

from typing import Any

import httpx

from view_agents_mcp.config import settings


class MultiAgentBridge:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.multi_agent_api_url or "").rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def health(self) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "MULTI_AGENT_API_URL not set"}
        with httpx.Client(base_url=self.base_url, timeout=10.0) as c:
            r = c.get("/health")
            r.raise_for_status()
            return {"ok": True, **r.json()}

    def create_workflow(
        self,
        *,
        order_id: str,
        after_sale_id: str,
        refund_amount: float,
        tenant: str = "T1",
    ) -> dict[str, Any]:
        if not self.enabled:
            return {"error": "MULTI_AGENT_API_URL not set"}
        with httpx.Client(base_url=self.base_url, timeout=30.0) as c:
            r = c.post(
                "/v1/workflows",
                json={
                    "tenant": tenant,
                    "order_id": order_id,
                    "after_sale_id": after_sale_id,
                    "refund_amount": refund_amount,
                },
            )
            r.raise_for_status()
            return r.json()

    def submit_proposal(
        self,
        *,
        workflow_id: str,
        tool: str,
        order_id: str,
        after_sale_id: str,
        amount: float,
        tenant: str = "T1",
        actor: str = "mcp-client",
        access_token: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return {"error": "MULTI_AGENT_API_URL not set"}
        token = access_token or settings.multi_agent_access_token
        with httpx.Client(base_url=self.base_url, timeout=30.0) as c:
            r = c.post(
                "/v1/proposals",
                json={
                    "workflow_id": workflow_id,
                    "tenant": tenant,
                    "tool": tool,
                    "order_id": order_id,
                    "after_sale_id": after_sale_id,
                    "amount": amount,
                    "actor": actor,
                    "approval_snapshot_id": "appr-default",
                    "access_token": token,
                },
            )
            r.raise_for_status()
            return r.json()