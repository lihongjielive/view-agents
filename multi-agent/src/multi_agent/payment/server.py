"""全功能支付 Mock（图 02/04/08 联调）。

关键点：
- POST /v1/refunds：按 business_key 幂等（重复 POST 返回同一 refund_id）
- GET：对账 / reconcile 路径（禁止 UNKNOWN 时盲 POST）
- /v1/admin/fault-injection：drop_response、timeout、late_callback 等（图 11）
- 线程安全内存态；测试用 reset_state() 清空
"""
from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="payment-mock", version="0.2.0")


class RefundState(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class FaultMode(str, Enum):
    NONE = "none"
    DROP_RESPONSE_AFTER_SUCCESS = "drop_response_after_success"
    TIMEOUT = "timeout"
    SLOW = "slow"
    FAIL_BUSINESS = "fail_business"
    LATE_CALLBACK = "late_callback"


class RefundRecord(BaseModel):
    business_key: str
    tenant: str
    order_id: str
    after_sale_id: str
    amount: float
    currency: str = "CNY"
    state: RefundState
    refund_id: str
    created_at: str
    updated_at: str
    idempotent_hit: bool = False
    failure_reason: str | None = None
    callback_url: str | None = None


class CreateRefundRequest(BaseModel):
    business_key: str
    order_id: str
    after_sale_id: str
    amount: float = Field(gt=0)
    currency: str = "CNY"
    callback_url: str | None = None


class FaultInjection(BaseModel):
    mode: FaultMode = FaultMode.NONE
    scope: str = "global"  # global | business_key
    business_key: str | None = None
    slow_ms: int = 2000
    late_callback_delay_ms: int = 1500


class _State:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.refunds: dict[str, RefundRecord] = {}
        self.post_count_by_key: dict[str, int] = {}
        self.global_fault = FaultMode.NONE
        self.per_key_fault: dict[str, FaultMode] = {}
        self.slow_ms = 2000
        self.late_callback_delay_ms = 1500
        self.callbacks: list[dict[str, Any]] = []
        self._late_cb: Callable[[str], None] | None = None


STATE = _State()


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _resolve_fault(business_key: str) -> FaultMode:
    if business_key in STATE.per_key_fault:
        return STATE.per_key_fault[business_key]
    return STATE.global_fault


def set_late_callback_hook(hook: Callable[[str], None] | None) -> None:
    STATE._late_cb = hook


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/admin/fault-injection")
def set_fault(body: FaultInjection) -> dict[str, Any]:
    with STATE._lock:
        if body.scope == "global":
            STATE.global_fault = body.mode
            STATE.slow_ms = body.slow_ms
            STATE.late_callback_delay_ms = body.late_callback_delay_ms
        elif body.business_key:
            STATE.per_key_fault[body.business_key] = body.mode
    return {"ok": True, "global": STATE.global_fault.value}


@app.delete("/v1/admin/fault-injection")
def clear_fault(business_key: str | None = None) -> dict[str, str]:
    with STATE._lock:
        if business_key:
            STATE.per_key_fault.pop(business_key, None)
        else:
            STATE.global_fault = FaultMode.NONE
            STATE.per_key_fault.clear()
    return {"status": "cleared"}


@app.get("/v1/admin/metrics")
def admin_metrics() -> dict[str, Any]:
    with STATE._lock:
        return {
            "refund_count": len(STATE.refunds),
            "post_attempts": dict(STATE.post_count_by_key),
            "global_fault": STATE.global_fault.value,
        }


# --- 核心业务：退款写入（Worker 唯一应调用的写接口）---

@app.post("/v1/refunds", response_model=RefundRecord)
def create_refund(
    body: CreateRefundRequest,
    x_tenant: str = Header(..., alias="X-Tenant"),
) -> RefundRecord:
    with STATE._lock:
        STATE.post_count_by_key[body.business_key] = (
            STATE.post_count_by_key.get(body.business_key, 0) + 1
        )
        existing = STATE.refunds.get(body.business_key)
        if existing:
            existing.idempotent_hit = True
            return existing.model_copy(deep=True)

        fault = _resolve_fault(body.business_key)
        if fault == FaultMode.FAIL_BUSINESS:
            rec = RefundRecord(
                business_key=body.business_key,
                tenant=x_tenant,
                order_id=body.order_id,
                after_sale_id=body.after_sale_id,
                amount=body.amount,
                currency=body.currency,
                state=RefundState.FAILED,
                refund_id=f"rf-{uuid.uuid4().hex[:8]}",
                created_at=_now(),
                updated_at=_now(),
                failure_reason="policy_rejected",
            )
            STATE.refunds[body.business_key] = rec
            return rec

        refund_id = f"rf-{uuid.uuid4().hex[:8]}"
        rec = RefundRecord(
            business_key=body.business_key,
            tenant=x_tenant,
            order_id=body.order_id,
            after_sale_id=body.after_sale_id,
            amount=body.amount,
            currency=body.currency,
            state=RefundState.SUCCEEDED,
            refund_id=refund_id,
            created_at=_now(),
            updated_at=_now(),
            callback_url=body.callback_url,
        )
        STATE.refunds[body.business_key] = rec

        if fault == FaultMode.SLOW:
            time.sleep(STATE.slow_ms / 1000.0)

        if fault == FaultMode.LATE_CALLBACK:

            def _late() -> None:
                time.sleep(STATE.late_callback_delay_ms / 1000.0)
                STATE.callbacks.append(
                    {"business_key": body.business_key, "state": "SUCCEEDED"}
                )
                if STATE._late_cb:
                    STATE._late_cb(body.business_key)

            threading.Thread(target=_late, daemon=True).start()

        if fault in (
            FaultMode.DROP_RESPONSE_AFTER_SUCCESS,
            FaultMode.TIMEOUT,
            FaultMode.LATE_CALLBACK,
        ):
            raise HTTPException(status_code=504, detail="gateway_timeout")

        return rec


@app.get("/v1/refunds/{business_key}", response_model=RefundRecord)
def get_refund(business_key: str) -> RefundRecord:
    with STATE._lock:
        rec = STATE.refunds.get(business_key)
        if not rec:
            raise HTTPException(status_code=404, detail="refund_not_found")
        return rec


@app.get("/v1/refunds", response_model=list[RefundRecord])
def list_refunds(
    tenant: str | None = None,
    order_id: str | None = None,
    state: RefundState | None = None,
) -> list[RefundRecord]:
    with STATE._lock:
        out = list(STATE.refunds.values())
    if tenant:
        out = [r for r in out if r.tenant == tenant]
    if order_id:
        out = [r for r in out if r.order_id == order_id]
    if state:
        out = [r for r in out if r.state == state]
    return out


@app.post("/v1/reconciliation/by-keys")
def reconciliation(keys: list[str]) -> dict[str, Any]:
    """Batch reconciliation (slide 08)."""
    with STATE._lock:
        found = []
        missing = []
        for k in keys:
            if k in STATE.refunds:
                found.append(STATE.refunds[k].model_dump())
            else:
                missing.append(k)
    return {"found": found, "missing": missing}


@app.get("/v1/admin/callbacks")
def list_callbacks() -> list[dict[str, Any]]:
    with STATE._lock:
        return list(STATE.callbacks)


def reset_state() -> None:
    with STATE._lock:
        STATE.refunds.clear()
        STATE.post_count_by_key.clear()
        STATE.global_fault = FaultMode.NONE
        STATE.per_key_fault.clear()
        STATE.callbacks.clear()


def main() -> None:
    import uvicorn

    uvicorn.run("multi_agent.payment.server:app", host="0.0.0.0", port=18080, reload=False)