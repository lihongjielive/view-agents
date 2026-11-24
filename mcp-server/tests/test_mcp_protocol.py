"""MCP 协议：resources / prompts / tools（in-process ASGI）。"""
from __future__ import annotations

import pytest
from fastmcp.utilities.tests import asgi_server

from view_agents_mcp.mcp_app import mcp

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def mcp_asgi():
    async with asgi_server(mcp, transport="streamable-http") as srv:
        yield srv


async def test_list_and_read_resources(mcp_asgi):
    async with mcp_asgi.client() as client:
        resources = await client.list_resources()
        uris = {str(r.uri) for r in resources}
        assert "view-agents://protocol/execution-summary" in uris
        assert "view-agents://multi-agent/gateway-codes" in uris
        body = await client.read_resource("view-agents://protocol/execution-summary")
        text = "".join(
            c.text for c in body if getattr(c, "text", None)
        )
        assert "business_key" in text


async def test_list_and_get_prompt(mcp_asgi):
    async with mcp_asgi.client() as client:
        prompts = await client.list_prompts()
        names = {p.name for p in prompts}
        assert "refund-after-sale-assist" in names
        result = await client.get_prompt(
            "refund-after-sale-assist",
            arguments={"order_id": "O-T", "after_sale_id": "AS-T"},
        )
        blob = str(result)
        assert "multi_agent_create_workflow" in blob
        assert "multi_agent_submit_proposal" in blob or "禁止" in blob


async def test_call_tool_ping(mcp_asgi):
    async with mcp_asgi.client() as client:
        result = await client.call_tool("mcp_ping", {})
        assert result.data.get("ok") is True
        assert result.data.get("socket_version")


async def test_catalog_and_describe(mcp_asgi):
    async with mcp_asgi.client() as client:
        cat = await client.call_tool("mcp_tools_catalog", {})
        assert cat.data.get("tools")
        name = cat.data["tools"][0]["name"]
        desc = await client.call_tool("mcp_tools_describe", {"name": name})
        assert desc.data.get("inputSchema")
        assert desc.data.get("name") == name


async def test_read_socket_manifest_resource(mcp_asgi):
    async with mcp_asgi.client() as client:
        body = await client.read_resource("view-agents://socket/manifest")
        text = "".join(c.text for c in body if getattr(c, "text", None))
        assert "socket_version" in text
        assert "plugs" in text