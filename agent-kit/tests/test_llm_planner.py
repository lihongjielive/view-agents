import json
from unittest.mock import patch

from agent_kit.planning import plan_demo, plan_with_llm


def test_plan_with_llm_no_key_falls_back(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert plan_with_llm("查询北京天气") == plan_demo("查询北京天气")


def test_plan_with_llm_parses_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    fake_json = json.dumps(
        {
            "steps": [
                {
                    "index": 1,
                    "description": "搜",
                    "kind": "tool",
                    "target": "search",
                    "arguments": {"query": "北京"},
                }
            ]
        }
    )

    class FakeMsg:
        content = fake_json

    with patch("langchain_openai.ChatOpenAI") as cls:
        cls.return_value.invoke.return_value = FakeMsg()
        steps = plan_with_llm("北京天气", "")
        assert len(steps) == 1
        assert steps[0].target == "search"