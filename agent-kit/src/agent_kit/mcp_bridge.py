"""MCP 桥 — 兼容 P0 API，委托 McpClient。"""
from __future__ import annotations

from typing import Any

from agent_kit.mcp_client import McpClient


def mcp_tools_call(
    name: str,
    arguments: dict | None = None,
    *,
    offline: bool = False,
) -> dict[str, Any]:
    return McpClient(offline=offline).call(name, arguments or {})