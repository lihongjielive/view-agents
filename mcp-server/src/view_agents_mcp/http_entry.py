"""Streamable HTTP 入口（P1）。"""
from __future__ import annotations

import asyncio
import os


async def _run() -> None:
    from view_agents_mcp.http_bearer import build_http_middlewares, expected_bearer_token
    from view_agents_mcp.mcp_app import mcp

    host = os.getenv("FASTMCP_HOST", "0.0.0.0")
    port = int(os.getenv("FASTMCP_PORT", "8010"))
    path = os.getenv("FASTMCP_STREAMABLE_HTTP_PATH", "/mcp")
    middleware = build_http_middlewares()
    if expected_bearer_token():
        import logging

        logging.getLogger(__name__).warning(
            "MCP_HTTP_BEARER_TOKEN is set; HTTP requires Authorization Bearer"
        )
    await mcp.run_http_async(
        host=host,
        port=port,
        transport="streamable-http",
        path=path,
        middleware=middleware or None,
        show_banner=True,
    )


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()