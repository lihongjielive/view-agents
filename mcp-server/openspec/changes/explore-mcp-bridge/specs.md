# Specs: MCP Server P1

## MCP-HTTP-1 Streamable HTTP 入口

- **SHALL** 提供 `view-agents-mcp-http` 脚本调用 `run_http_async`。  
- **SHALL** 支持 env：`FASTMCP_HOST`、`FASTMCP_PORT`（默认 8010）、`FASTMCP_STREAMABLE_HTTP_PATH`（默认 `/mcp`）。  
- **SHOULD** 文档说明与 stdio 二选一部署，不同时混用 stdout 日志。

## MCP-OAUTH-1 路线图

- **SHALL** 维护 `docs/oauth-roadmap.md` 含 Phase 0–3。  
- **MAY** P1 实现 Phase 0：`MCP_HTTP_BEARER_TOKEN` 设置时校验 HTTP 请求 Bearer。  
- **SHALL NOT** P1 声称完整 OAuth 2.1 已生产就绪。

## MCP-CONTRACT-1 LangGraph 对齐

- **SHALL** `contracts/multi_agent_tools.json` 列出与 `ma-api` 映射的工具。  
- **SHALL** MCP 实现的 tool `name` 与契约 `name` 一致。  
- **SHALL** LangGraph stub tools（可选 env）使用相同 `name` 与参数语义。  
- **SHALL NOT** LangGraph tool 直接 `PaymentClient.post_refund`。

## MCP-PROTO-1 Resources

- **SHALL** `resources/list` 包含：
  - `view-agents://protocol/execution-summary`
  - `view-agents://multi-agent/gateway-codes`
- **SHALL** `resources/read` 返回 `text/markdown` 正文非空。  
- **SHALL** `tests/test_mcp_protocol.py` 断言上述 URI。

## MCP-PROTO-2 Prompts

- **SHALL** `prompts/list` 包含 `refund-after-sale-assist`。  
- **SHALL** `prompts/get` 返回消息含 `multi_agent_create_workflow` 与禁止直写支付文案。  
- **SHALL** `tests/test_mcp_protocol.py` 断言。

## MCP-TOOL-1 既有 Tools（回归）

- **SHALL** `mcp_ping`、`multi_agent_submit_proposal` 在 ASGI 测试中仍可 `call_tool`。  
- **SHALL** `multi_agent_submit_proposal` annotations 含 `readOnlyHint: true`。

## MCP-SEC-1

- **SHALL** stdio 模式不向 stdout 写非 JSON-RPC 行。  
- **SHALL** `mcp_server_info` 不返回明文 token。