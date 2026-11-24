"""图节点：llm（思考/规划）与 action（工具执行 / 观测）。"""

from agent.nodes.action import take_action
from agent.nodes.llm import make_llm_node

# 文件声明的是 agent.nodes 包对外公开的符号有两个
# make_llm_node： 工厂函数：创建 LLM 节点（nodes/llm.py）
# take_action： action 节点 函数：执行 tool_calls（nodes/action.py）
# make_llm_node(agent) → 注册为图节点 "llm"
#  take_action → 注册为图节点 "action"
__all__ = ["make_llm_node", "take_action"]

# 角色
# llm.py:  想：读历史 + 用户话，调 LLM
# action.py: 做：执行 tool_calls

# 写入消息
# llm.py: HumanMessage（本轮）、AIMessage
# action.py: ToolMessage（工具结果）

# 是否调真实 API
# llm.py:  是（Chat 模型）
# action.py: 否（只调本地 @tool 函数）


# llm.py = 大模型推理节点：组上下文、调绑定了工具的 Chat 模型，把输出写回 AgentState.messages，并清空已消费的 input。
# 它是 Agent 每一轮「思考」的入口，也是 START 之后、以及每次工具跑完再回到图里的那个节点。