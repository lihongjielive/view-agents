# Proposal: view-agents MCP Server（P1 扩展）

> **Status:** `apply` — P1 已完成（2026-11-24）  
> **Change id:** `explore-mcp-bridge`  
> **前置:** [explore.md](./explore.md) 已归档结论

## 背景

`mcp-server` P0 已提供 **stdio** FastMCP：Tools 桥接 `ma-api`，Resources/Prompts 骨架，与 `langgraph-agent` / `multi-agent` 弱耦合。

P1 目标：团队可共享 **HTTP 传输**、OAuth 有清晰路线图、**LangGraph 工具名与 MCP 契约统一**、CI 覆盖 **resources/read** 与 **prompts/get**。

## 目标

### P0（已完成）

- FastMCP stdio、`view-agents-mcp` 入口  
- Tools：`mcp_ping`、`multi_agent_*`（proposal-only）  
- Resources ×2、Prompt `refund-after-sale-assist`  
- Tool Annotations、`docs/mcp-fundamentals.md`、`usage-scenarios.md`

### P1 — 本提案范围

| # | 能力 | 说明 |
|---|------|------|
| 1 | **Streamable HTTP** | `view-agents-mcp-http`；env `FASTMCP_*`；文档与冒烟测 |
| 2 | **OAuth 路线图** | `docs/oauth-roadmap.md`：Phase0 env token → Phase1 Bearer 校验 → Phase2 OAuth 2.1 |
| 3 | **契约统一** | `contracts/multi_agent_tools.json` + `docs/langgraph-mcp-contract.md`；LangGraph 可选 stub tools |
| 4 | **协议测试** | `pytest`：`list_resources` / `read_resource` / `list_prompts` / `get_prompt`（in-process ASGI） |

### P2（非阻塞）

- 真实 OAuth 授权服务器、scope 裁剪 `tools/list`  
- LangGraph 默认启用 multi-agent tools 替代部分 mock tools  
- Resource `subscribe`、远程部署样板  

## Non-goals

- 不在 P1 实现完整 IdP / 多租户 OAuth 产品化  
- MCP 不替代 `ma-api` 鉴权真相；OAuth 后仍以 Gateway `access_token` 为准  
- 不接入真实支付  

## 成功标准（P1 归档）

1. `cd mcp-server && pip install -e ".[dev]" && pytest -q` 含 `test_mcp_protocol.py` 全绿  
2. `view-agents-mcp-http` 本地可启，`GET /health` 或 MCP discover 成功（见 design）  
3. `contracts/multi_agent_tools.json` 与 `tool-catalog.md`、`langgraph` stub 字段一致  
4. `docs/oauth-roadmap.md` 评审通过（Phase 勾选自洽）  

## 风险与假设

- FastMCP 4.x `run_http_async` API 随版本微调；pin `fastmcp>=2,<5` 或测最新 4.x  
- 协议测试依赖 `pytest-asyncio` + `fastmcp.utilities.tests.asgi_server`  
- LangGraph 全量切换 tools 影响演示 ReAct；P1 仅 **旁路 optional** `multi_agent` 模块  

## 交付物

| 产物 | 路径 |
|------|------|
| 规格 | [specs.md](./specs.md) |
| 设计 | [design.md](./design.md) |
| 任务 | [tasks.md](./tasks.md) |
| OAuth 路线 | `docs/oauth-roadmap.md` |
| 契约 | `contracts/`、`docs/langgraph-mcp-contract.md` |

## 下一步

**`/opsx:apply`** 按 [tasks.md](./tasks.md) 顺序实施 P1 四项。