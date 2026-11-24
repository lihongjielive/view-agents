"""条件边：图示「循环控制 / exists_action」。"""
from __future__ import annotations

from typing import Literal

from langgraph.graph import END

from agent.state import AgentState

# 条件边返回值 → route_map 中的节点名（LangGraph 条件路由惯例）
ROUTE_ACTION = "action"
ROUTE_END = "end"

# llm  ──→  exists_action(?)  ──→ action  （有工具要调）
#  └──→  exists_action(?)  ──→ END     （直接给终答）
def exists_action(state: AgentState) -> Literal["action", "end"]:
    """
    读取 llm 节点刚写入的最后一条 AIMessage：

    - 含 tool_calls → 进入 action 节点（图示「需要迭代」）
    - 否则 → END（图示「任务完成 / 终答」）
    """
    messages = state.get("messages") or []
    if not messages:
        return ROUTE_END

    last = messages[-1]
    tool_calls = getattr(last, "tool_calls", None) or []
    if tool_calls:
        return ROUTE_ACTION
    return ROUTE_END


def route_map() -> dict:
    """条件边分支名 → 实际图节点（或 LangGraph END 常量）。"""
    return {ROUTE_ACTION: "action", ROUTE_END: END}