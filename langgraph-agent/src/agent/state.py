"""AgentState：LangGraph 各节点共享的状态（图示「状态节点」）。"""
from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph import add_messages
# ---------------------------------------------------------------------------
# TypedDict 是 Python 类型系统里用来描述**“固定键名、每键有明确类型”的字典**的结构化类型，常在 typing（3.8+）和 typing_extensions（旧版本或需要新特性时）里使用
# 普通写法 dict[str, int] 只表示「键是 str、值是 int」，不能说明有哪些键；TypedDict 可以写成类似「带类型注解的 dict」
# from typing_extensions import NotRequired, Required
# class Config(TypedDict):
#     host: str
#     port: NotRequired[int]
# ---------------------------------------------------------------------------
from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# 为什么需要 TypedDict + add_messages？
# - LangGraph 的 StateGraph 在每个节点执行后，会按字段规则「归约」状态更新。
# - messages 使用 add_messages：新消息与历史 append 合并，而不是整表覆盖。
# - 这与图示中的 chat_history / 多轮工具往返一致。
# ---------------------------------------------------------------------------

#  AgentState 是这个 LangGraph 项目的全局状态 schema：整张图共享同一份「字典状」状态，各节点只读需要的字段、只返回要改的字段局部更新。
#  # total=False：键都可缺省
class AgentState(TypedDict, total=False):
    """图示 AgentState：input、messages、intermediate_steps、flags。"""

    # 本轮用户输入（CLI 每轮写入；llm 节点消费后可清空，避免重复入历史）；入口写入；llm 消费后清空
    input: str

    # 对话 + 工具往返（Human / AI / ToolMessage），由 add_messages 归约
    # add_messages 是 LangGraph 里的状态归约函数（reducer），专门用在 StateGraph 的 messages 字段上，用来决定「节点返回的新消息」如何与「图里已有的消息列表」合并
    # 对 messages 这个键不用默认的「整段覆盖」，而是每次更新都调用 add_messages(旧列表, 节点返回的新消息) 得到合并后的列表
    #  追加：新消息会接到历史后面（多轮对话、工具调用往返就靠这个）。
    #  按 ID 更新：若新消息的 id 与已有消息相同，会替换那条消息，而不是再 append 一条（适合流式输出、人机改消息等）。
    #  格式兼容：能把 dict 形式（如 {"role": "user", "content": "..."}）规范成 LangChain 的 HumanMessage / AIMessage / ToolMessage 等
    #  add_messages(left: 当前 state 里的 messages, right: 节点 return 里的 messages) -> 新的 messages 列表
    messages: Annotated[list, add_messages]

    # 审计轨迹：(工具名, 工具返回文本)，便于调试与展示中间步骤
    # list[tuple[str, str]] 是 Python 的类型注解，描述「列表里每个元素都是一个二元组，且两个元素都是 str」
    # list[...] ： 列表 /  tuple[str, str] ：长度为 2 的元组：第 1 个是 str，第 2 个也是 str
    intermediate_steps: list[tuple[str, str]]

    # 扩展标记：如 max_iterations、debug 等（本 change P2 可用）
    flags: dict[str, Any]