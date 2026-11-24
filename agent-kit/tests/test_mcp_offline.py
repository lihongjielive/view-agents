from agent_kit.mcp_bridge import mcp_tools_call


def test_mcp_ping_offline():
    out = mcp_tools_call("mcp_ping", offline=True)
    assert out.get("ok") is True