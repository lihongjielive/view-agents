"""编译 LangGraph StateGraph（图示：节点 + 边 + 循环 + 历史存储）。"""
from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph

from agent.agent_framework import Agent, default_agent
from agent.edges import exists_action, route_map
from agent.nodes.action import take_action
from agent.nodes.llm import make_llm_node
from agent.state import AgentState

#  Agent 的装配中心：把状态、节点、边拼成一张可执行的 LangGraph StateGraph，并 compile 成 CLI / API 调用的 graph 对象。
# 1、选用 Agent 配置（默认 default_agent()）
# 2、创建 StateGraph(AgentState)
# 3、注册节点、连边
# 4、可选挂上 MemorySaver（多轮会话）
# 5、return builder.compile(...) → 得到可调 invoke / stream 的图
def build_graph(agent: Agent | None = None, *, checkpointer: bool = True):
    """
    构建并编译 Agent 图。

    拓扑（与 architecture-flow.png 一致）：
        START → llm → exists_action ─┬→ action → llm（循环）
                                     └→ END（无 tool_calls）

    checkpointer=True 时使用 MemorySaver + CLI 的 thread_id 做会话历史（图示历史存储）。
    """
    agent = agent or default_agent()

    # StateGraph(AgentState)：全图节点读写同一状态 schema
    # LangGraph 在节点执行后把 return {...} 合并进全局 state（messages 走 add_messages，其它键默认覆盖）。
    builder = StateGraph(AgentState)

    # 蓝圈：LLM 推理节点（工厂注入 Agent 配置）
    builder.add_node("llm", make_llm_node(agent))
    # 橙圈：工具执行节点
    builder.add_node("action", take_action)
    # 固定边：入口先进 llm；action 做完一定回到 llm（ReAct 环）
    builder.add_edge(START, "llm")
    # 红菱：条件边，由 exists_action 决定下一跳，决定去 action 还是 END
    builder.add_conditional_edges("llm", exists_action, route_map())
    # 行动完成后回到 LLM，形成 ReAct 环
    builder.add_edge("action", "llm")
    # checkpointer=True（默认）：进程内 MemorySaver，配合 CLI/API 的 thread_id，多轮 chat 能接着上一轮 messages
    # checkpointer=False：测试里常用，不存 checkpoint，图更轻
    memory = MemorySaver() if checkpointer else None
    return builder.compile(checkpointer=memory)