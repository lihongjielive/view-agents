"""经 MCP 的售后退款提议演示（不直连支付 POST）。"""
from __future__ import annotations

from typing import Any

from agent_kit.mcp_client import McpClient


def run_refund_demo(
    order_id: str,
    after_sale_id: str,
    refund_amount: float = 99.0,
    *,
    offline: bool = False,
) -> dict[str, Any]:
    mcp = McpClient(offline=offline)
    health = mcp.call("multi_agent_health")
    wf = mcp.call(
        "multi_agent_create_workflow",
        {
            "order_id": order_id,
            "after_sale_id": after_sale_id,
            "refund_amount": refund_amount,
        },
    )
    workflow_id = wf.get("workflow_id")
    if not workflow_id:
        return {
            "health": health,
            "workflow": wf,
            "error": "no_workflow_id",
            "hint": "确认 ma-api 与 MCP 已启动（见 docs/mcp-host-guide.md）",
        }
    proposal = mcp.call(
        "multi_agent_submit_proposal",
        {
            "workflow_id": workflow_id,
            "tool": "refund.create",
            "order_id": order_id,
            "after_sale_id": after_sale_id,
            "amount": refund_amount,
        },
    )
    return {
        "health": health,
        "workflow": wf,
        "proposal": proposal,
        "note": "执行在 multi-agent Worker；禁止 agent-kit 直写支付退款 POST。",
    }