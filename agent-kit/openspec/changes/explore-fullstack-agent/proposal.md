# Proposal: agent-kit（P0 归档 → P1 生态集成）

> **Status:** `apply` — P1 已完成（2026-11-24）  
> **Change id:** `explore-fullstack-agent`  
> **前置:** [explore.md](./explore.md)（探索结论）、P0 代码已落地

## 背景

P0 已在 monorepo 新增 **`agent-kit/`**，与 `langgraph-agent`、`multi-agent`、`mcp-server` 并列，交付教材 **8 步骨架**、规则规划、`mcp_bridge` 离线 mock、`DataAnalysisAgent` 与 CI（8 tests）。

P1 目标：把 agent-kit 从 **教学离线骨架** 升级为 **可连真 MCP + 可选 LLM 规划 + 契约对齐**，形成教材中 **MCP Host → Client → Server → multi-agent** 的端到端故事，且仍保持无 API Key 时 pytest 全绿。

## 目标

### P0（已完成）

| # | 能力 | 状态 |
|---|------|------|
| 1 | 目录与 CLI（`init-info` / `run` / `analyze` / `mcp-ping`） | 已交付 |
| 2 | tools / skills / memory / prompts | 已交付 |
| 3 | `KitAgent` 规则 `plan_demo` | 已交付 |
| 4 | `DataAnalysisAgent` + sample CSV | 已交付 |
| 5 | 根 README + `view-agents-ci` agent-kit job | 已交付 |

### P1 — 本提案范围

| # | 能力 | 说明 |
|---|------|------|
| 1 | **MCP Client 强化** | 读 `mcp-server/contracts/unified_socket.json`；实现 `tools/list` 缓存 + `mcp_tools_catalog` / `mcp_tools_describe` / `multi_agent_health` 调用；HTTP 集成测（ASGI 或 live 标记） |
| 2 | **LLM 规划（可选）** | `OPENAI_API_KEY` 存在时 `plan_with_llm`，否则回落 `plan_demo`；结构化输出 `PlanStep` JSON |
| 3 | **售后演示链路** | CLI `agent-kit refund-demo`：经 MCP 调用 `multi_agent_create_workflow` + `submit_proposal`（需 `ma-api`）；文档一键启动顺序 |
| 4 | **记忆增强** | 规划前向量检索 `prompts/examples.md` + 会话摘要写入 SQLite；`agent-kit memory-search "关键词"` |
| 5 | **契约与文档** | `docs/mcp-host-guide.md`；与 `mcp-server/docs/langgraph-mcp-contract.md` 交叉链接；`settings.json` 增加 `socket_contract_path` |

### P2（非阻塞）

- MCP **stdio 子进程** Client（对齐 Cursor Host，不依赖 HTTP）
- Chroma / pgvector 替换词袋向量
- **A2A** Agent 间协议调研稿（仅文档，不实现）
- LangGraph 子图调用 `KitAgent` 作为 preprocessor 节点
- 教案流程图 PDF 导出至 `agent-kit/docx/`

## Non-goals

- 不替代 `langgraph-agent` 的 StateGraph 执行引擎  
- 不在 P1 实现完整 OAuth Client（沿用 `MCP_HTTP_BEARER_TOKEN` + mcp-server 路线图）  
- 不直连支付退款 POST；提议仍仅经 `multi_agent_*` / Gateway  
- 不做 Coze / 飞书文档同步  

## 成功标准（P1 归档）

1. `cd agent-kit && pip install -e ".[dev]" && pytest -q` 全绿，且新增 `tests/test_mcp_integration.py`（离线 mock + 可选 `@pytest.mark.live`）  
2. `agent-kit mcp-catalog` 输出与 `unified_socket.json` 中 plug 工具名一致（抽样断言）  
3. 未设置 `OPENAI_API_KEY` 时行为与 P0 相同；设置后 `agent-kit run --llm` 产生 ≥1 步有效 plan  
4. `docs/mcp-host-guide.md` 描述：终端 1 `ma-api`、终端 2 `view-agents-mcp-http`、终端 3 `agent-kit refund-demo`（PowerShell `;` 分隔）  
5. monorepo 根 README OpenSpec 链接指向本 proposal P1  

## 风险与假设

- MCP HTTP JSON-RPC 形态随 FastMCP 版本变化；P1 以 `mcp-server` 现有 ASGI 测试为真源  
- `multi_agent_*` live 测试依赖端口 18082/8010，CI 默认仅跑离线层  
- LLM 规划增加 flake；测试 mock `ChatOpenAI` 或使用 `langchain` fake  

## 交付物

| 产物 | 路径 |
|------|------|
| 规格 | [specs.md](./specs.md) |
| 设计 | [design.md](./design.md) |
| 任务 | [tasks.md](./tasks.md) |
| Host 指南 | `docs/mcp-host-guide.md`（apply 时创建） |
| 契约引用 | `../mcp-server/contracts/unified_socket.json`（只读） |

## 四项目分工（P1 后）

| 项目 | agent-kit P1 触点 |
|------|-------------------|
| `mcp-server` | MCP Server；契约 `unified_socket.json` |
| `multi-agent` | `ma-api` 工作流与提议 |
| `langgraph-agent` | 同工具名；可选 `USE_MULTI_AGENT_TOOLS` 对照实验 |
| `agent-kit` | **MCP Host 教学 Client** + 规划/记忆 |

## 下一步

**`/opsx:apply`** 按 [tasks.md](./tasks.md) 自顶向下实施 P1 五项。