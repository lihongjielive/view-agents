# Tasks: explore-mcp-bridge（/opsx:apply）

> **提案:** [proposal.md](./proposal.md) · **规格:** [specs.md](./specs.md)

## P0 — explore 骨架（已完成）

- [x] FastMCP stdio、`view-agents-mcp`
- [x] Tools + Annotations + ma-api 桥接
- [x] Resources ×2、Prompt `refund-after-sale-assist`
- [x] `explore.md`、`mcp-fundamentals.md`、`usage-scenarios.md`

---

## P1 — 本 propose 范围

### 1. HTTP 传输（MCP-HTTP-1）

- [x] `http_entry.py` + `view-agents-mcp-http` 脚本
- [x] `env.example` / README HTTP 段落
- [x] `test_mcp_protocol` ASGI streamable-http 冒烟

### 2. OAuth 路线图（MCP-OAUTH-1）

- [x] `docs/oauth-roadmap.md`（Phase 0–3）
- [x] Phase 0：HTTP Bearer 可选校验（`MCP_HTTP_BEARER_TOKEN`）

### 3. LangGraph 契约（MCP-CONTRACT-1）

- [x] `contracts/multi_agent_tools.json`
- [x] `docs/langgraph-mcp-contract.md`
- [x] `langgraph-agent`：`tools/multi_agent.py` + `USE_MULTI_AGENT_TOOLS`

### 4. 协议测试（MCP-PROTO-1/2）

- [x] `pytest-asyncio` dev 依赖
- [x] `tests/test_mcp_protocol.py`：resources + prompts + tool 回归

### 5. 门禁

- [x] `pyproject` `[dev]` 含 asyncio
- [x] CI：`.github/workflows/view-agents-ci.yml` + `scripts/ci.ps1`

---

## P2 — 可选

- [ ] OAuth 2.1 + scope 裁剪 `tools/list`
- [ ] LangGraph 默认启用 multi_agent tools
- [x] `mcp-server` 纳入根 `.github/workflows`（view-agents-ci）

## apply 约定

`cd mcp-server && pip install -e ".[dev]" && pytest -q` 全绿后勾选 P1。