"""Action 节点：图示「行动 + 观测」（执行 tool_calls，写回 ToolMessage）。"""
from __future__ import annotations

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from agent.state import AgentState
from agent.tools import ALL_TOOLS

# 启动时构建 name → tool 索引，action 内按 LLM 给的 name 分发
# llm → exists_action ──有 tool_calls──→ action ──→ 回到 llm
#                    └──无 tool_calls──→ END
# llm：模型输出 AIMessage，可能带 tool_calls（要调哪些工具、参数是什么）
# action.py：按这些 tool_calls 调 Python 工具，产出 ToolMessage
# 再回到 llm：模型读到工具结果，继续推理或给出终答
# 对应注册在 graph.py：builder.add_node("action", take_action)


_tools_by_name = {t.name: t for t in ALL_TOOLS}

#1、读状态：取 messages 最后一条（应是带 tool_calls 的 AIMessage）
#2、逐个执行 tool_calls：
#  用 name 在 ALL_TOOLS 建好的字典 _tools_by_name 里找工具
#  用 args 调用 tool.invoke(args, config)
#  未知工具名则返回错误文案
#3、写回状态（局部更新）：
#  messages：追加多条 ToolMessage（tool_call_id 必须和 AI 里那条 call 的 id 一致）
#  intermediate_steps：追加 (工具名, 返回字符串) 做审计/调试

# 决定要不要调工具、调哪个： llm 节点 + 模型
# 路由到 action 还是结束： edges.py 的 exists_action
# 工具具体逻辑：src/agent/tools/*.py（如 search_questions）
# action.py 只做 调度 + 执行 + 把结果塞回 AgentState。

# AIMessage(tool_calls=[{name: "search_questions", args: {keywords: "会议"}, id: "1"}])
#          ↓ take_action
#      ToolMessage(tool_call_id="1", content="搜索「会议」: 找到 3 条…")
#          ↓ add_messages 合并进 state
#      下一轮 llm 把 ToolMessage 当上下文继续 invoke

# action.py = 工具执行节点：把 LLM 的「行动意图」变成真实函数调用和 ToolMessage，让 Agent 能完成 想 → 做 → 再想 的循环
def take_action(state: AgentState, config: RunnableConfig) -> dict:
    """
    1. 取 messages 末尾 AIMessage 的 tool_calls（行动输入）。
    2. 调用 Function 工具库（图示右侧虚线框）。
    3. 每个结果写 ToolMessage（观测），供下一轮 llm 读取并继续推理。
    4. 同步更新 intermediate_steps 便于 CLI -v 或后续审计。
    """
    messages = state.get("messages") or []
    # 对话里最新一条消息
    last = messages[-1]
    # getattr(对象, "属性名", 默认值)：
    # 若 last 有 tool_calls 属性 → 返回它的值（通常是 list[dict]，或 LangChain 里的结构化 call）
    # 若没有该属性 → 返回 None（不会抛 AttributeError）
    # 为什么要用 getattr 而不是 last.tool_calls？
    #    messages 里不只有 AIMessage，还可能有 HumanMessage、ToolMessage 等，不一定都有 tool_calls
    #    类型不统一或老数据时，直接 .tool_calls 可能报错；getattr 更稳
    tool_calls = getattr(last, "tool_calls", None) or []

    steps: list[tuple[str, str]] = list(state.get("intermediate_steps") or [])
    out_messages: list[ToolMessage] = []

    # 遍历 tool_calls，逐个执行并生成 ToolMessage
    for tc in tool_calls:
        name = tc["name"]
        args = tc.get("args") or {}
        tool = _tools_by_name.get(name)
        if tool is None:
            content = f"Unknown tool: {name}"
        else:
            content = str(tool.invoke(args, config))
        steps.append((name, content))
        # tool_call_id 必须与 AIMessage 中 id 对应，否则下一轮模型无法对齐
        out_messages.append(
            ToolMessage(content=content, tool_call_id=tc["id"], name=name)
        )

    return {"messages": out_messages, "intermediate_steps": steps}