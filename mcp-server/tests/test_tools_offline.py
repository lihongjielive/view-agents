"""不依赖 ma-api 的离线 smoke。"""
from __future__ import annotations

from view_agents_mcp.bridges.multi_agent import MultiAgentBridge
from view_agents_mcp.config import Settings


def test_bridge_disabled_without_url():
    b = MultiAgentBridge("")
    assert not b.enabled
    assert b.health()["ok"] is False


def test_settings_masked_no_token():
    s = Settings(multi_agent_api_url="http://x", multi_agent_access_token="secret", langgraph_api_url=None)
    m = s.masked()
    assert "secret" not in str(m)