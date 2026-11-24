"""图路由与 action 节点单元测试（无真实 LLM 调用）。"""
from langchain_core.messages import AIMessage, HumanMessage

from agent.edges import exists_action
from agent.nodes.action import take_action
from agent.state import AgentState


def test_exists_action_routes_to_action():
    state: AgentState = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "search_questions", "args": {"keywords": "x"}, "id": "1"}
                ],
            )
        ]
    }
    assert exists_action(state) == "action"


def test_exists_action_routes_to_end():
    state: AgentState = {"messages": [AIMessage(content="done")]}
    assert exists_action(state) == "end"


def test_take_action_mock_tool():
    state: AgentState = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "book_meeting",
                        "args": {
                            "title": "sync",
                            "start_time": "tomorrow 2pm",
                        },
                        "id": "tc1",
                    }
                ],
            )
        ],
        "intermediate_steps": [],
    }
    out = take_action(state, {})
    assert "mtg-1001" in out["messages"][0].content
    assert out["intermediate_steps"][0][0] == "book_meeting"


def test_build_graph_compiles():
    """Smoke: graph compiles without OPENAI_API_KEY (lazy LLM init)."""
    from agent.graph import build_graph

    g = build_graph(checkpointer=False)
    assert g is not None