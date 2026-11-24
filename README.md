# view-agents

LangGraph 演示与生产级 Multi-Agent 执行协议对照 monorepo。

| 目录 | 说明 |
|------|------|
| [`langgraph-agent/`](langgraph-agent/) | 单图 ReAct + 内存状态 + LLM 工具循环（演示） |
| [`multi-agent/`](multi-agent/) | 可恢复执行协议：SQLite Store、Gateway、Worker、支付 Mock（生产仿真） |
| [`mcp-server/`](mcp-server/) | 通用 FastMCP（stdio），可选桥接 `ma-api` 提议层 |
| [`agent-kit/`](agent-kit/) | 0→1 Agent 骨架：prompts / 规划 / 记忆 / tools / skills / MCP Client |

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
```

OpenSpec：`mcp-server/openspec/changes/explore-mcp-bridge/proposal.md`；`agent-kit/openspec/changes/explore-fullstack-agent/proposal.md`（**P1 apply 完成**）。

文档与 OpenSpec 见各子项目 `README.md`、`openspec/`。