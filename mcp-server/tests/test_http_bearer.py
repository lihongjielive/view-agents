"""HTTP Bearer Phase 0。"""
from __future__ import annotations

import pytest
from fastmcp.utilities.tests import asgi_server

from view_agents_mcp.http_bearer import build_http_middlewares
from view_agents_mcp.mcp_app import mcp

pytestmark = pytest.mark.asyncio


@pytest.fixture
def bearer_env(monkeypatch):
    monkeypatch.setenv("MCP_HTTP_BEARER_TOKEN", "test-bearer-secret")


async def test_bearer_rejects_without_header(bearer_env):
    mw = build_http_middlewares()
    async with asgi_server(mcp, transport="streamable-http", middleware=mw) as srv:
        async with srv.http_client() as http:
            r = await http.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            assert r.status_code == 401


async def test_bearer_accepts_valid_header(bearer_env):
    mw = build_http_middlewares()
    async with asgi_server(mcp, transport="streamable-http", middleware=mw) as srv:
        async with srv.client(headers={"Authorization": "Bearer test-bearer-secret"}) as client:
            result = await client.call_tool("mcp_ping", {})
            assert result.data.get("ok") is True


async def test_no_bearer_env_allows_anonymous(monkeypatch):
    monkeypatch.delenv("MCP_HTTP_BEARER_TOKEN", raising=False)
    async with asgi_server(mcp, transport="streamable-http") as srv:
        async with srv.client() as client:
            result = await client.call_tool("mcp_ping", {})
            assert result.data.get("ok") is True