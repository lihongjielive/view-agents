"""FAQ 搜索 mock 工具。"""
from langchain_core.tools import tool


# 用 LangChain 把普通 Python 函数声明成「LLM 可调用的工具」的写法
# @tool 来自 langchain_core.tools 的装饰器
# 函数会变成「工具对象」（有 name、description、参数 schema 等），而不只是普通 def
# 给模型做 function calling：llm.bind_tools(ALL_TOOLS) 会把这些工具的名字、说明、参数类型发给模型，模型在需要时可以生成 tool_calls，
#    例如 {"name": "search_questions", "args": {"keywords": "会议"}}
# 在 action 节点真正执行：take_action 按 name 找到工具，再 tool.invoke(args) 调用你的函数，把返回值放进 ToolMessage

# keywords: str    工具参数：类型注解会进 JSON Schema，模型知道要传字符串 keywords
# -> str         返回值是字符串，会作为 ToolMessage 的 content 给下一轮 LLM 看
# """搜索常见问题。keywords: 搜索词。"""   工具描述，模型靠它判断什么时候该调这个工具

# 用户问题
#    → LLM 可能输出 AIMessage(tool_calls=[search_questions, ...])
#    → action 调用 search_questions.invoke({"keywords": "..."})
#    → ToolMessage(返回的那段 str)
#    → LLM 再根据 ToolMessage 组织最终回答
@tool
def search_questions(keywords: str) -> str:
    """搜索常见问题。keywords: 搜索词。"""
    return (
        f"搜索「{keywords}」: 找到 3 条相似问题，"
        "怎么做:「如何预定会议？」"
    )