"""邮件 mock 工具。"""
from langchain_core.tools import tool

# @tool：把 Python 函数注册成 LangChain/LangGraph 可绑定、可调用的工具
@tool
def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件。to: 收件人; subject: 主题; body: 正文。"""
    return f"已向 {to} 发送邮件，主题「{subject}」。"