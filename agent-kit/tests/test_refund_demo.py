import pytest

from agent_kit.refund_demo import run_refund_demo


def test_refund_demo_offline_chain():
    out = run_refund_demo("O1", "A1", 10.0, offline=True)
    assert out["workflow"].get("workflow_id")
    assert out["proposal"].get("code") or out["proposal"].get("mode")


@pytest.mark.live
def test_refund_demo_live_optional():
    """本地需 ma-api + view-agents-mcp-http。"""
    out = run_refund_demo("O1", "A1", 10.0, offline=False)
    assert "workflow" in out