# view-agents

LangGraph 演示与生产级 Multi-Agent 执行协议对照 monorepo。

| 目录 | 说明 |
|------|------|
| [`langgraph-agent/`](langgraph-agent/) | 单图 ReAct + 内存状态 + LLM 工具循环（演示） |
| [`multi-agent/`](multi-agent/) | 可恢复执行协议：SQLite Store、Gateway、Worker、支付 Mock（生产仿真） |
| [`mcp-server/`](mcp-server/) | 通用 FastMCP（stdio），可选桥接 `ma-api` 提议层 |
| [`agent-kit/`](agent-kit/) | 0→1 Agent 骨架：prompts / 规划 / 记忆 / tools / skills / MCP Client |
| [`agent-memory/`](agent-memory/) | 四种记忆：会话检查点、摘要压缩、事实画像、向量检索 |

## 快速开始

```bash
# LangGraph 演示
cd langgraph-agent
pip install -e ".[dev]"
# 复制 env.example → .env 后
agent run "查一下会议室"

# Multi-Agent 协议仿真
cd multi-agent
pip install -e ".[dev,langgraph]"
pytest -q
ma-demo figure-01

# MCP（stdio 或 HTTP）
cd mcp-server
pip install -e ".[dev]"
view-agents-mcp              # stdio
view-agents-mcp-http         # http://0.0.0.0:8010/mcp

# Agent 0→1 骨架（第四项目）
cd agent-kit
pip install -e ".[dev]"
agent-kit init-info
agent-kit run "查询北京天气"
agent-kit analyze tests/fixtures/sample.csv

# Agent 四种记忆（第五项目）
cd agent-memory
pip install -e ".[dev]"
agent-memory demo-report
```

OpenSpec：`mcp-server/.../explore-mcp-bridge` · `agent-kit/.../explore-fullstack-agent` · [`agent-memory/.../explore-four-memories`](agent-memory/openspec/changes/explore-four-memories/proposal.md)（**P1 apply 完成**）。

文档与 OpenSpec 见各子项目 `README.md`、`openspec/`。