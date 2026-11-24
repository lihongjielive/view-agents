# Tasks: build-langgraph-agent-full-workflow

> **Status:** archived · 主路径已实现；5.2 / P2 见 `ARCHIVE.md`

按顺序执行；`/opsx:apply` 时只做未勾选项。

## 1. 工程元数据

- [x] 1.1 新增 `pyproject.toml`（与已安装 `langgraph-agent==0.1.0` 元数据一致：依赖、console_scripts `agent`）
- [x] 1.2 新增 `README.md`、`env.example`（`.env.example` 若被 ignore 则用 `env.example`）
- [x] 1.3 补齐 `src/agent/__init__.py`、`nodes/__init__.py`

## 2. 状态与框架（图示 AgentState + Agent 类）

- [x] 2.1 实现 `agent/state.py`：`AgentState` + `add_messages` reducer
- [x] 2.2 实现 `agent/agent_framework.py`：`Agent` 类、`default_agent()` 中文 system prompt

## 3. 节点与边（图示 llm / action / exists_action）

- [x] 3.1 实现 `agent/nodes/llm.py`：`make_llm_node(agent)`，OpenAI `ChatOpenAI`，`bind_tools`
- [x] 3.2 确认 `agent/nodes/action.py` 与 `agent/edges.py` 与 design 一致（小改即可）
- [x] 3.3 确认 `agent/graph.py` 编译逻辑与 `MemorySaver`

## 4. 工具库（图示 Function 库）

- [x] 4.1 新增 `agent/tools/meetings.py`：`book_meeting`、`cancel_meeting` mock（满足现有 pytest `mtg-1001` 约定）
- [x] 4.2 核对 `tools/__init__.py` 导出 `ALL_TOOLS`

## 5. CLI

- [x] 5.1 核对 `agent/cli.py`：`run` / `chat` / `new-thread`，加载 `dotenv`，无 Key 时友好退出
- [ ] 5.2 本地手册验证：`agent run "查询 LangGraph 文档并总结"`（需真实 Key，由使用者执行）

## 6. 测试与验收

- [x] 6.1 `pytest` 全绿（无需网络）
- [x] 6.2 在 tasks 勾选完成项；README 中补充「图结构」与图示对照一句

## P2（可选，本 change 不做除非时间允许）

- [ ] P2.1 `flags.max_iterations` 在 `exists_action` 或 llm 前熔断
- [ ] P2.2 集成测试 mark + GitHub Actions workflow