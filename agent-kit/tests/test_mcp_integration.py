from agent_kit.mcp_client import McpClient


def test_catalog_offline_has_mcp_ping_and_multi_agent():
    cat = McpClient(offline=True).catalog()
    names = {t["name"] for t in cat.get("tools", [])}
    assert "mcp_ping" in names
    assert any(n.startswith("multi_agent_") for n in names)


def test_describe_offline_workflow_tool():
    desc = McpClient(offline=True).describe("multi_agent_create_workflow")
    assert desc.get("name") == "multi_agent_create_workflow"
    assert desc.get("inputSchema")