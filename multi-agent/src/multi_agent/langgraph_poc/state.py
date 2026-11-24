"""LangGraph PoC 状态（非 AgentState.messages 真相源）。"""
from __future__ import annotations

from typing import TypedDict


class PocState(TypedDict, total=False):
    """提议图状态；业务真相在 SQLite Store。"""

    workflow_id: str
    tenant: str
    order_id: str
    after_sale_id: str
    refund_amount: float
    coupon_amount: float
    refund_proposal_code: str
    refund_allowed: bool
    coupon_proposal_code: str
    coupon_allowed: bool
    refund_executed: bool
    coupon_executed: bool
    error: str