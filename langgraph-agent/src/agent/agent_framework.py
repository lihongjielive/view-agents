"""Agent 框架类：封装「大脑」侧 system prompt 与模型参数（图示创建 Agent 框架）。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

# 默认人设：与 design 中「中文友好秘书 + 工具使用准则」一致
_DEFAULT_SYSTEM = """你是一个高效、友好的办公助理 Agent。
你可以调用工具完成：预订/取消会议、查询文档、搜索常见问题、发送邮件（均为模拟接口）。

要求：
1. 先理解用户意图，再决定是否调用工具；能一步说清的不要滥用工具。
2. 调用工具前在心里规划参数；工具返回后整合成简洁中文答复。
3. 无法完成时诚实说明，不要编造工具结果。
"""

# 用法：
# agent = Agent()                          # 全默认
# agent = Agent(temperature=0.7)           # 只改一项
# agent = default_agent()                  # 工厂里 return Agent()
@dataclass
class Agent:
    """
    图示 Agent 类：self.system 为系统提示，供 llm 节点每轮推理时注入。

    模型名可从环境变量 OPENAI_MODEL 读取，便于 .env 配置而不改代码。
    """

    system: str = field(default_factory=lambda: _DEFAULT_SYSTEM)
    model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "qwen3.8-flash")
    )
    temperature: float = 0.0


def default_agent() -> Agent:
    """构造默认 Agent 实例，供 build_graph / CLI 使用。"""
    return Agent()