# agent-kit

**第四并列项目**：从 0 到 1 搭建可扩展 Agent（教材 8 步 — 提示词 / 规划 / 记忆 / 工具 / 技能 / MCP / 数据分析实战）。

| 教材模块 | 路径 |
|----------|------|
| 配置 | `env.example`、`settings.json` |
| 定义 Agent | `agents/agent.yaml`、`agents/agent.py` |
| 工具 | `src/agent_kit/tools/` |
| 技能 | `src/agent_kit/skills/` |
| 记忆 | `src/agent_kit/memory/`（SQLite + 内存向量） |
| 提示词 | `prompts/*.md` |
| MCP Client | `src/agent_kit/mcp_client.py` → `mcp-server` |

与 monorepo 关系：

- **大模型**：`agent-kit run --llm` 需 `OPENAI_API_KEY`；否则规则 `plan_demo`
- **MCP**：`view-agents-mcp-http` + `MULTI_AGENT_API_URL`
- **执行真相**：`multi-agent`（经 MCP `multi_agent_*`）

OpenSpec：`openspec/changes/explore-fullstack-agent/explore.md`

## 快速开始

```powershell
cd agent-kit
pip install -e ".[dev]"
copy env.example .env   # 可选

agent-kit init-info
agent-kit run "查询北京天气并推荐活动"
agent-kit analyze tests/fixtures/sample.csv
agent-kit mcp-ping
agent-kit mcp-catalog
agent-kit mcp-describe multi_agent_create_workflow
agent-kit refund-demo ORD-001 AS-001
agent-kit memory-search 旅行
agent-kit mcp-ping --live   # 需先启动 view-agents-mcp-http
pytest -q
```

三终端联调见 [`docs/mcp-host-guide.md`](docs/mcp-host-guide.md)。

### 四种记忆（agent-memory 可选）

```powershell
pip install -e ..\agent-memory
$env:AGENT_KIT_USE_COORDINATOR = "1"
$env:AGENT_KIT_USER_ID = "user-001"
agent-kit run "写报告要附来源"
```

`run` 结束输出中的 `memory_session_id` 可用于 `agent-memory session-resume`。

## 数据分析 Agent

`DataAnalysisAgent` 含教材中的 `AnalysisTask` 与四引擎：`DataProcessor`、`ModelManager`、`VisualizationEngine`、`ReportGenerator`。

文档映射：`docs/agent-stack-map.md`