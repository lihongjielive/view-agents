"""LLM 节点：图示「思考 + 行动输入」（bind_tools 产出 tool_calls 或终答）。"""
from __future__ import annotations

import os
from typing import Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from agent.agent_framework import Agent
from agent.state import AgentState
from agent.tools import ALL_TOOLS

# 节点函数类型：LangGraph 传入 (state, config) -> 局部状态更新 dict
LlmNode = Callable[[AgentState, RunnableConfig], dict]

# 负责调用大模型做推理——要么直接回答用户，要么生成 带 tool_calls 的 AIMessage，交给后面的 action 节点执行工具。
# START → llm ⇄ action → …
#          ↓
#      exists_action → 无工具则 END
def make_llm_node(agent: Agent) -> LlmNode:
    """
    工厂函数：根据 Agent 配置创建绑定了工具库的 ChatOpenAI 节点。

    流程（与 design §3 一致）：
    1. 若有 state["input"]，追加 HumanMessage（用户本轮话语）。
    2. SystemMessage + 历史 messages 调用模型（已 bind_tools）。
    3. 返回 AIMessage：可能含 tool_calls（走 action）或纯文本（走 END）。
    """

    # 延迟创建模型客户端：build_graph / pytest 编译阶段不要求 OPENAI_API_KEY
    bound_llm = None  # ChatOpenAI.bind_tools 后的 Runnable，首调 invoke 时再初始化

    def llm_node(state: AgentState, config: RunnableConfig) -> dict:
        # nonlocal 是 Python 的作用域关键字：在嵌套函数里，标明某个名字不是局部变量，而是要去改外层（非全局）函数里的那个变量。
        nonlocal bound_llm
        if bound_llm is None:
            # 支持 OpenAI 兼容网关：OPENAI_BASE_URL + OPENAI_API_KEY（如阿里云 MaaS）
            llm_kwargs: dict = {
                "model": agent.model,
                "temperature": agent.temperature,
            }
            if key := os.getenv("OPENAI_API_KEY"):
                llm_kwargs["api_key"] = key
            if base := os.getenv("OPENAI_BASE_URL"):
                llm_kwargs["base_url"] = base.rstrip("/")
            bound_llm = ChatOpenAI(**llm_kwargs).bind_tools(ALL_TOOLS)
        # 把 search_questions、book_meeting 等工具的 schema 交给模型，模型才能在 AIMessage 里填 tool_calls。
        #  edges.exists_action 根据最后一条 AI 有没有 tool_calls 决定走 action 还是结束。
        prior = list(state.get("messages") or [])
        batch: list = []

        # llm_node — 每次进节点时做的事
        # 将「本轮 input」并入消息流；清空 input 防止同一句重复进入多轮
        # 读 state["input"]，非空则变成 HumanMessage 放进本轮 batch
        user_text = (state.get("input") or "").strip()
        if user_text:
            batch.append(HumanMessage(content=user_text))

        # 拼 prompt：模型上下文 = 系统人设 + 历史 + 本轮用户句
        prompt = [SystemMessage(content=agent.system)] + prior + batch
        # 得到一条 AIMessage
        ai: AIMessage = bound_llm.invoke(prompt, config)

        # add_messages 会把 batch + ai 依次 append 到 state.messages
        return {"messages": batch + [ai], "input": ""}

    return llm_node