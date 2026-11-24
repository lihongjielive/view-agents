"""Function 工具库聚合（图示工具列表），供 llm bind_tools 与 action 查找。"""
from agent.tools.docs import query_documentation
from agent.tools.email import send_email
from agent.tools.meetings import book_meeting, cancel_meeting
from agent.tools.search import search_questions

# 真实变量：工具对象列表
ALL_TOOLS = [
    book_meeting,
    cancel_meeting,
    query_documentation,
    search_questions,
    send_email,
]

# __all__ 是 Python 模块级的一个约定变量：声明「这个包在 from 包 import * 时，允许导出哪些名字」
# 字符串列表：声明模块的「公开导出名单」，不是业务数据
__all__ = ["ALL_TOOLS"]