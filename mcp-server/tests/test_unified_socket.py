"""契约与插口元工具。"""
from __future__ import annotations

import pytest

from view_agents_mcp.contract import (
    assert_tool_allowed,
    catalog_entries,
    get_tool,
    load_socket_manifest,
    tool_index,
)

REGISTERED_TOOL_NAMES = {
    "mcp_ping",
    "mcp_server_info",
    "mcp_tools_catalog",
    "mcp_tools_describe",
    "multi_agent_health",
    "multi_agent_create_workflow",
    "multi_agent_submit_proposal",
    "langgraph_agent_status",
}


def test_contract_covers_all_registered_tools():
    names = set(tool_index())
    assert names == REGISTERED_TOOL_NAMES


def test_plugs_reference_existing_tools():
    manifest = load_socket_manifest()
    all_names = set(tool_index())
    for plug in manifest["plugs"]:
        for name in plug["tools"]:
            assert name in all_names


def test_forbidden_pattern():
    with pytest.raises(ValueError):
        assert_tool_allowed("payment_post_refund")


def test_catalog_shorter_than_describe():
    cat = catalog_entries()
    for row in cat:
        full = get_tool(row["name"])
        assert full
        assert len(row["catalogSummary"]) <= len(full.description)


def test_manifest_resource_uri_listed():
    uris = {r["uri"] for r in load_socket_manifest()["resources"]}
    assert "view-agents://socket/manifest" in uris