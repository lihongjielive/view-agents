"""支付 Mock 客户端。

- base_url=`asgi://payment`：pytest 进程内 TestClient，无网络
- 否则：httpx 连独立 payment-mock 进程（docker / CLI）
- 504 → kind=timeout，驱动 Task UNKNOWN（图 02）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx
from starlette.testclient import TestClient

from multi_agent.payment.server import app


@dataclass
class PaymentClient:
    base_url: str = "http://127.0.0.1:18080"
    timeout: float = 5.0
    _test_client: TestClient | None = field(default=None, repr=False)

    def _ensure_test_client(self) -> TestClient:
        if self._test_client is None:
            self._test_client = TestClient(app)
        return self._test_client

    def post_refund(
        self,
        *,
        tenant: str,
        business_key: str,
        order_id: str,
        after_sale_id: str,
        amount: float,
    ) -> tuple[str, dict[str, Any] | None, Exception | None]:
        """Returns (kind, body_or_none, err). kind: ok | timeout | error"""
        if self.base_url == "asgi://payment":
            c = self._ensure_test_client()
            r = c.post(
                "/v1/refunds",
                headers={"X-Tenant": tenant},
                json={
                    "business_key": business_key,
                    "order_id": order_id,
                    "after_sale_id": after_sale_id,
                    "amount": amount,
                },
            )
            if r.status_code == 504:
                return ("timeout", None, None)
            if r.status_code >= 400:
                return ("error", None, httpx.HTTPStatusError("error", request=None, response=None))
            return ("ok", r.json(), None)

        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as c:
                r = c.post(
                    "/v1/refunds",
                    headers={"X-Tenant": tenant},
                    json={
                        "business_key": business_key,
                        "order_id": order_id,
                        "after_sale_id": after_sale_id,
                        "amount": amount,
                    },
                )
                if r.status_code == 504:
                    return ("timeout", None, None)
                r.raise_for_status()
                return ("ok", r.json(), None)
        except httpx.TimeoutException as e:
            return ("timeout", None, e)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 504:
                return ("timeout", None, None)
            return ("error", None, e)

    def get_refund(self, business_key: str) -> dict[str, Any] | None:
        if self.base_url == "asgi://payment":
            c = self._ensure_test_client()
            r = c.get(f"/v1/refunds/{business_key}")
            if r.status_code == 404:
                return None
            return r.json()

        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as c:
            r = c.get(f"/v1/refunds/{business_key}")
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()

    def set_fault(self, mode: str, scope: str = "global", business_key: str | None = None) -> None:
        if self.base_url == "asgi://payment":
            c = self._ensure_test_client()
            c.post(
                "/v1/admin/fault-injection",
                json={"mode": mode, "scope": scope, "business_key": business_key},
            )
            return
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            client.post(
                "/v1/admin/fault-injection",
                json={"mode": mode, "scope": scope, "business_key": business_key},
            )

    def reconciliation_by_keys(self, keys: list[str]) -> dict:
        if self.base_url == "asgi://payment":
            c = self._ensure_test_client()
            r = c.post("/v1/reconciliation/by-keys", json=keys)
            r.raise_for_status()
            return r.json()
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            r = client.post("/v1/reconciliation/by-keys", json=keys)
            r.raise_for_status()
            return r.json()

    def clear_fault(self, business_key: str | None = None) -> None:
        if self.base_url == "asgi://payment":
            c = self._ensure_test_client()
            c.delete("/v1/admin/fault-injection", params={"business_key": business_key or ""})
            return
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            client.delete(
                "/v1/admin/fault-injection", params={"business_key": business_key or None}
            )