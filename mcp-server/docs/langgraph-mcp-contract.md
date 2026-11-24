# LangGraph 与 MCP 工具契约

**事实源：** [`../contracts/unified_socket.json`](../contracts/unified_socket.json)（唯一插口契约；`multi_agent_tools.json` 已废弃）

## 原则

1. **同名同参**：LangGraph `@tool` 的 `name` 与 MCP `tools/list` 一致（下划线风格）。  
2. **同 HTTP 映射**：两者均调用 `ma-api`，不共享 Python import。  
3. **禁止支付直写**：契约内无 `post_refund` 类工具。

## 对照表

| name | LangGraph（P1） | MCP | ma-api |
|------|-----------------|-----|--------|
| `multi_agent_health` | `tools/multi_agent.py` | `server.py` | GET `/health` |
| `multi_agent_create_workflow` | 同上 | 同上 | POST `/v1/workflows` |
| `multi_agent_submit_proposal` | 同上 | 同上 | POST `/v1/proposals` |

## LangGraph 启用

```bash
set USE_MULTI_AGENT_TOOLS=1
set MULTI_AGENT_API_URL=http://127.0.0.1:18082
agent run "为订单 O1 建单并提议退款 10 元"
```

默认 `USE_MULTI_AGENT_TOOLS=0` 保留办公 mock tools，现有 `test_graph.py` 不变。

## Host 侧（Cursor）

`mcp.json` 使用同名 tools；模型在 Cursor 与 LangGraph CLI 间迁移时 **描述与 schema 一致**，降低幻觉参数。

## 变更流程

1. 改 `contracts/multi_agent_tools.json`  
2. 同步 `mcp-server` tool 签名与 `tool-catalog.md`  
3. 同步 `langgraph-agent/tools/multi_agent.py` docstring / 参数  
4. 跑 `mcp-server pytest` + `langgraph-agent pytest`