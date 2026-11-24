# langgraph-agent

基于 LangGraph 的 Agent 全流程示例：**状态 → LLM → 条件边 → 工具 → 循环 → 终答**，与 `openspec/.../design.md` 及架构图 PNG 一致。

## 图结构

`START` → `llm` → `exists_action` → (`action` → `llm`)* → `END`

架构配图：`docs/assets/architecture-flow.png`（1920×1080）。

文档：[AgentState 使用说明](docs/agent-state.md)

并列工程：[multi-agent](../multi-agent)、[mcp-server](../mcp-server) — 生产协议与 MCP 工具面（Supervisor + 持久状态 + 支付 Mock，与本文演示互补）。其中 [LangGraph PoC](../multi-agent/docs/langgraph-poc.md) 演示：**本仓负责 LLM 循环，multi-agent 负责 Gateway/Worker 执行**。

## 目录

```
src/agent/
├── state.py           # AgentState（messages + add_messages）
├── agent_framework.py # Agent / system prompt
├── graph.py           # StateGraph 编译 + MemorySaver
├── edges.py           # exists_action 条件边
├── nodes/llm.py       # 思考 + bind_tools
├── nodes/action.py    # 工具执行（观测）
├── tools/             # mock 工具库
└── cli.py             # agent run | chat
```

## 环境

```bash
cd langgraph-agent
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

复制 `env.example` 为 `.env` 后填写（项目根 `langgraph-agent/.env`，已 gitignore）：

- `OPENAI_API_KEY`（必填）
- `OPENAI_BASE_URL`（选填，OpenAI 兼容网关，如阿里云 MaaS）
- `OPENAI_MODEL`（默认 `qwen3.8-flash`；未设则用代码默认值）

## 启动入口说明

| 层级 | 入口 | 说明 |
|------|------|------|
| 命令行 | `agent.cli:app`（Typer） | `pip install -e .` 后命令为 `agent` |
| HTTP | `agent.api:app`（FastAPI） | `pip install -e ".[api]"` 后 `agent-serve` |
| 图逻辑 | `agent.graph.build_graph()` | 编程/CLI/API 共用，**不是 class，是工厂函数** |
| 框架配置 | `agent.agent_framework.Agent` | system prompt、model 参数 |

## 使用

### CLI

```bash
agent run "帮我查询 LangGraph 文档并总结"
agent run -v "订明天下午两点的会"
agent chat --thread my-session
agent new-thread
pytest
```

### HTTP 接口

```bash
pip install -e ".[api]"
agent-serve
# 默认 http://0.0.0.0:8000 ；可用 AGENT_HOST / AGENT_PORT 覆盖
```

```bash
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/v1/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"查询 LangGraph 文档并总结\", \"thread_id\": \"demo\"}"
```

在线文档：启动后访问 `http://127.0.0.1:8000/docs`

## 开发说明

实现过程在源码中以中文注释标注各节点与图示的对应关系；设计已归档：`openspec/changes/archive/2026-11-23-build-langgraph-agent-full-workflow/design.md`。