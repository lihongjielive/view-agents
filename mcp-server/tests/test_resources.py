from view_agents_mcp.resources_static import read_uri


def test_read_execution_summary():
    text = read_uri("view-agents://protocol/execution-summary")
    assert "business_key" in text
    assert "提议" in text