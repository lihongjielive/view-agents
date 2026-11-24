# Tasks: explore-fullstack-agent

## P0 — 教材骨架（已完成）

- [x] OpenSpec explore / proposal 初稿
- [x] 脚手架：pyproject、env、settings.json、README
- [x] agents / tools / skills / memory / prompts
- [x] Core `KitAgent` + `plan_demo` + `mcp_bridge` 离线
- [x] `DataAnalysisAgent` + sample CSV + tests
- [x] 根 README + CI `agent-kit` job

## P1 — `/opsx:apply`（已完成 2026-11-24）

### 1. MCP Client + 契约

- [x] 新增 `mcp_client.py` + `contract_loader.py`（读 `unified_socket.json`）
- [x] 扩展 `config.py` / `settings.json`：`contract_path`
- [x] CLI：`mcp-catalog`、`mcp-describe`
- [x] `tests/test_mcp_integration.py`（离线契约 fallback + catalog 断言）
- [x] `mcp_bridge.py` 委托 `McpClient`（保持 offline API）

### 2. LLM 规划

- [x] `planning.py`：`plan_with_llm` + 解析与回落
- [x] CLI `run --llm`；README 说明 API Key
- [x] `tests/test_llm_planner.py`（mock invoke）

### 3. refund-demo 端到端

- [x] CLI `refund-demo` 参数与 MCP 调用链
- [x] `@pytest.mark.live` 集成测（可选本地）
- [x] `docs/mcp-host-guide.md` 三终端说明

### 4. 记忆增强

- [x] 启动索引 `examples.md`；`run()` 注入向量 context
- [x] CLI `memory-search`
- [x] `tests/test_memory.py` 补充检索用例

### 5. 文档与收尾

- [x] `proposal.md` Status → P1 apply 完成
- [x] 根 `README.md` OpenSpec 链接
- [x] `explore.md` 探索结论更新

## P2（ backlog，本 change 不勾选）

- [ ] MCP stdio 子进程 Client
- [ ] 向量库 Chroma 可选依赖
- [ ] A2A 调研文档