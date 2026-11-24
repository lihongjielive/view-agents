# Specs: agent-kit P1

## KIT-MCP-1 契约对齐

- **SHALL** 从 `unified_socket.json` 加载工具名列表（或通过 MCP `mcp_tools_catalog` 获取）。  
- **SHALL** `McpClient.call` 的 `name` 与契约 `tools[].name` 一致（如 `multi_agent_create_workflow`）。  
- **SHALL NOT** P1 引入契约外 tool 名到默认 `agent.yaml`。

## KIT-MCP-2 HTTP 调用

- **SHALL** 使用 `MCP_HTTP_URL` 发送 `tools/call` JSON-RPC。  
- **MAY** 设置 `MCP_HTTP_BEARER_TOKEN` 时附加 Bearer Header。  
- **SHALL** 连接失败返回结构化 `error`（含 `url`），不抛未捕获异常到 CLI 顶层。  
- **SHALL** 离线模式（默认测试）不发起 HTTP。

## KIT-MCP-3 CLI 暴露

- **SHALL** 提供 `agent-kit mcp-catalog [--plug core|multi_agent]`。  
- **SHALL** 提供 `agent-kit mcp-describe <name>`。  
- **SHALL** `tests/test_mcp_integration.py` 断言 catalog 含 `mcp_ping` 与至少一个 `multi_agent_*`（契约 fallback）。

## KIT-PLAN-1 LLM 规划

- **SHALL** `--llm` 在无 API Key 时报错并 exit code ≠ 0，或打印明确提示后回落规则（实现二选一时须在 README 写明；**推荐** 无 Key 时拒绝 `--llm`）。  
- **SHALL** LLM 输出解析为 `list[PlanStep]`，非法 JSON 回落 `plan_demo`。  
- **SHALL** 单元测试 mock LLM，不依赖网络。

## KIT-DEMO-1 售后演示

- **SHALL** `agent-kit refund-demo` 接受 `order_id`、`after_sale_id`、可选 `refund_amount`。  
- **SHALL** live 模式下依次调用 MCP `multi_agent_create_workflow` 与 `multi_agent_submit_proposal`（`tool=refund.create`）。  
- **SHALL** stdout 含 Gateway 返回字段或 `error` 说明。  
- **SHALL NOT** 调用支付 mock 的退款 POST。

## KIT-MEM-1 检索增强

- **SHALL** `KitAgent.run` 将向量检索结果拼入 task context（非空时）。  
- **SHALL** `agent-kit memory-search <query>` 返回 top-k 文本片段。  
- **SHOULD** 检索不影响 P0 测试断言（weather demo 仍触发 search 步骤）。

## KIT-DOC-1

- **SHALL** `docs/mcp-host-guide.md` 含三终端启动说明（PowerShell `;`）。  
- **SHALL** 链接 `mcp-server/docs/langgraph-mcp-contract.md` 与 `unified_socket.json`。

## KIT-REG-1 回归

- **SHALL** P0 八项测试保持通过。  
- **SHALL** `mcp_bridge.mcp_tools_call(..., offline=True)` 保持向后兼容至 P2。