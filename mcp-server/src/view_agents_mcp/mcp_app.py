"""统一插口：契约注册 Tools / Resources / Prompts。"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any

from fastmcp import FastMCP

from view_agents_mcp import __version__
from view_agents_mcp.bridges.multi_agent import MultiAgentBridge
from view_agents_mcp.config import settings
from view_agents_mcp.contract import (
    catalog_entries,
    get_tool,
    load_socket_manifest,
    tool_index,
)
from view_agents_mcp.resources_static import read_uri

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

_manifest = load_socket_manifest()

mcp = FastMCP(
    name=_manifest.get("title", "view-agents-mcp"),
    instructions=(
        "统一 MCP 插口（Model Context Protocol）："
        "优先 mcp_tools_catalog 短目录，再 mcp_tools_describe 取完整标签。"
        "multi_agent_* 仅提议/建单，禁止支付 POST。"
        f" 契约版本 socket={_manifest.get('socket_version')}."
    ),
    version=__version__,
)


def _spec_annotations(name: str) -> dict[str, bool] | None:
    spec = get_tool(name)
    return spec.annotations() if spec else None


@mcp.tool(annotations=_spec_annotations("mcp_ping"))
def mcp_ping() -> dict[str, Any]:
    spec = get_tool("mcp_ping")
    return {
        "ok": True,
        "service": "view-agents-mcp",
        "version": __version__,
        "socket_version": _manifest.get("socket_version"),
        "description": spec.description if spec else "",
    }


@mcp.tool(annotations=_spec_annotations("mcp_server_info"))
def mcp_server_info() -> dict[str, Any]:
    return {
        "version": __version__,
        "socket_version": _manifest.get("socket_version"),
        "plugs": _manifest.get("plugs", []),
        "bridges": settings.masked(),
        "tool_count": len(tool_index()),
    }


@mcp.tool(annotations=_spec_annotations("mcp_tools_catalog"))
def mcp_tools_catalog(plug_id: str | None = None) -> dict[str, Any]:
    """短目录：应对「标签过多」— Host/模型可先读此项再 describe。"""
    return {
        "socket_version": _manifest.get("socket_version"),
        "plug_id_filter": plug_id,
        "tools": catalog_entries(plug_id=plug_id),
    }


@mcp.tool(annotations=_spec_annotations("mcp_tools_describe"))
def mcp_tools_describe(name: str) -> dict[str, Any]:
    spec = get_tool(name)
    if not spec:
        return {"error": "unknown_tool", "name": name, "hint": "call mcp_tools_catalog"}
    return spec.describe_payload()


@mcp.tool(annotations=_spec_annotations("multi_agent_health"))
def multi_agent_health(base_url: str | None = None) -> dict[str, Any]:
    return MultiAgentBridge(base_url).health()


@mcp.tool(annotations=_spec_annotations("multi_agent_create_workflow"))
def multi_agent_create_workflow(
    order_id: str,
    after_sale_id: str,
    refund_amount: float,
    tenant: str = "T1",
    base_url: str | None = None,
) -> dict[str, Any]:
    return MultiAgentBridge(base_url).create_workflow(
        tenant=tenant,
        order_id=order_id,
        after_sale_id=after_sale_id,
        refund_amount=refund_amount,
    )


@mcp.tool(annotations=_spec_annotations("multi_agent_submit_proposal"))
def multi_agent_submit_proposal(
    workflow_id: str,
    tool: str,
    order_id: str,
    after_sale_id: str,
    amount: float,
    tenant: str = "T1",
    actor: str = "mcp-client",
    access_token: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    if tool not in ("refund.create", "coupon.issue"):
        return {"error": "invalid_tool", "allowed": ["refund.create", "coupon.issue"]}
    return MultiAgentBridge(base_url).submit_proposal(
        workflow_id=workflow_id,
        tool=tool,
        order_id=order_id,
        after_sale_id=after_sale_id,
        amount=amount,
        tenant=tenant,
        actor=actor,
        access_token=access_token,
    )


@mcp.tool(annotations=_spec_annotations("langgraph_agent_status"))
def langgraph_agent_status() -> dict[str, str]:
    if settings.langgraph_api_url:
        return {"status": "configured", "url": settings.langgraph_api_url}
    return {"status": "not_configured", "hint": "set LANGGRAPH_API_URL"}


@mcp.resource(
    uri="view-agents://protocol/execution-summary",
    name="execution-protocol-summary",
    mime_type="text/markdown",
    description="四层身份、提议 vs 执行",
)
def resource_execution_summary() -> str:
    return read_uri("view-agents://protocol/execution-summary")


@mcp.resource(
    uri="view-agents://multi-agent/gateway-codes",
    name="gateway-t03-codes",
    mime_type="text/markdown",
    description="Tool Gateway 裁决代码表",
)
def resource_gateway_codes() -> str:
    return read_uri("view-agents://multi-agent/gateway-codes")


@mcp.resource(
    uri="view-agents://socket/manifest",
    name="unified-socket-manifest",
    mime_type="application/json",
    description="完整 unified_socket.json（供 Host 校验契约版本）",
)
def resource_socket_manifest() -> str:
    return json.dumps(load_socket_manifest(), ensure_ascii=False, indent=2)


@mcp.prompt(
    name="refund-after-sale-assist",
    description="售后退款+补券：先 catalog → describe → 建单 → 提议",
)
def prompt_refund_after_sale(
    order_id: str = "ORD-EXAMPLE",
    after_sale_id: str = "AS-EXAMPLE",
) -> str:
    return f"""你是售后助手（view-agents 统一 MCP 插口）：

0. 可先 mcp_tools_catalog，再 mcp_tools_describe 取参数细节（省上下文）。
1. multi_agent_create_workflow（order_id={order_id}, after_sale_id={after_sale_id}）。
2. multi_agent_submit_proposal，tool=refund.create；解释 Gateway code。
3. 退款 Worker 完成前发券可能 T03_DEP。
4. **禁止**任何支付退款 POST；执行在 multi-agent Worker。
5. resources: view-agents://protocol/execution-summary
"""