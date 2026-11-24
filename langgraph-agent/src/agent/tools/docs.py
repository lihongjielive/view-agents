"""文档查询 mock 工具。"""
from langchain_core.tools import tool

# @tool 来自 langchain_core.tools 的装饰器
# 是用 LangChain 把普通 Python 函数声明成「LLM 可调用的工具」的写法
# 1、函数会变成「工具对象」（有 name、description、参数 schema 等），而不只是普通 def
# 2、给模型做 function calling：llm.bind_tools(ALL_TOOLS) 会把这些工具的名字、说明、参数类型发给模型，模型在需要时可以生成 tool_calls，
# 例如 {"name": "search_questions", "args": {"keywords": "会议"}}。
# 3、在 action 节点真正执行：take_action 按 name 找到工具，再 tool.invoke(args) 调用你的函数，把返回值放进 ToolMessage。
@tool
def query_documentation(query: str) -> str:
    """查询内部文档。query: 检索关键词或问题。"""
    return (
        f"文档检索「{query}」命中 2 条：\n"
        "1. LangGraph 使用 StateGraph 定义节点与条件边。\n"
        "2. Agent 状态通常包含 messages 与 tool 往返记录。"
    )