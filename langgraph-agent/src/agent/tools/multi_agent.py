"""multi-agent ma-api 工具 — 与 MCP 统一插口同名（contracts/unified_socket.json）。"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
from langchain_core.tools import tool

_SOCKET_JSON = (
    Path(__file__).resolve().parents[4] / "mcp-server" / "contracts" / "unified_socket.json"
)


@lru_cache(maxsize=1)
def _tool_descriptions() -> dict[str, str]:
    if not _SOCKET_JSON.is_file():
        return {}
    data = json.loads(_SOCKET_JSON.read_text(encoding="utf-8"))
    return {t["name"]: t["description"] for t in data.get("tools", []) if "name" in t}


def _desc(name: str, fallback: str) -> str:
    return _tool_descriptions().get(name, fallback)


def _base_url() -> str:
    return os.getenv("MULTI_AGENT_API_URL", "http://127.0.0.1:18082").rstrip("/")


def _token() -> str:
    return os.getenv("MULTI_AGENT_ACCESS_TOKEN", "token-valid")


@tool(
    "multi_agent_health",
    description=_desc("multi_agent_health", "探测 multi-agent GET /health。"),
)
def multi_agent_health(base_url: str | None = None) -> str:
    url = (base_url or _base_url()).rstrip("/")
    try:
        with httpx.Client(base_url=url, timeout=10.0) as c:
            r = c.get("/health")
            r.raise_for_status()
            return json.dumps(r.json(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


@tool(
    "multi_agent_create_workflow",
    description=_desc(
        "multi_agent_create_workflow",
        "创建 refund+coupon workflow；不触发支付 POST。",
    ),
)
def multi_agent_create_workflow(
    order_id: str,
    after_sale_id: str,
    refund_amount: float,
    tenant: str = "T1",
) -> str:
    try:
        with httpx.Client(base_url=_base_url(), timeout=30.0) as c:
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
            return json.dumps(r.json(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool(
    "multi_agent_submit_proposal",
    description=_desc(
        "multi_agent_submit_proposal",
        "提交 Gateway 提议；仅返回 allow/code/reason。",
    ),
)
def multi_agent_submit_proposal(
    workflow_id: str,
    tool: str,
    order_id: str,
    after_sale_id: str,
    amount: float,
    tenant: str = "T1",
    actor: str = "langgraph-agent",
) -> str:
    try:
        with httpx.Client(base_url=_base_url(), timeout=30.0) as c:
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
                    "access_token": _token(),
                },
            )
            r.raise_for_status()
            return json.dumps(r.json(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


MULTI_AGENT_TOOLS: list[Any] = [
    multi_agent_health,
    multi_agent_create_workflow,
    multi_agent_submit_proposal,
]