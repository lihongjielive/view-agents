"""stdio 入口（统一插口实现见 mcp_app.py）。"""
from __future__ import annotations

from view_agents_mcp.mcp_app import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()