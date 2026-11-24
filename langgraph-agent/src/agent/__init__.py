"""LangGraph 演示 Agent（与 multi-agent 生产协议对照）。

关键点：
- `state.AgentState`：messages + add_messages 归约（非业务真相）
- `graph.build_graph`：START→llm⇄action ReAct 环
- `nodes.llm`：bind_tools 产出 tool_calls
- `nodes.action`：ToolMessage 回填
- `edges.exists_action`：有无 tool_calls 路由
- 生产写操作应对接 multi-agent `POST /v1/proposals`，禁止 tool 内直写支付
"""

from agent.graph import build_graph

__all__ = ["build_graph"]
__version__ = "0.1.0"