# Agent 技术栈对照（教材插图 → view-agents）

| 教材概念 | agent-kit 实现 | 兄弟项目 |
|----------|----------------|----------|
| 提示词 | `prompts/system.md` 等 | — |
| 智能体（规划/记忆/工具） | `KitAgent` + `planning.py` | `langgraph-agent` 图循环 |
| 大模型 | `OPENAI_API_KEY`（可选） | 两仓共用 langchain-openai |
| MCP 连接标准 | `mcp_client.py` / Host 指南 | `mcp-server` |
| Multi-Agent 生态 | MCP `multi_agent_*` | `multi-agent` |
| 数据分析实战 | `DataAnalysisAgent` | 独立 CLI `agent-kit analyze` |