# MCP Host 三终端启动（agent-kit）

agent-kit 作 **MCP Host**：经 HTTP Client 调用 `mcp-server`，再由 Server 桥接 `ma-api`。

契约真源：[mcp-server/contracts/unified_socket.json](../../mcp-server/contracts/unified_socket.json)  
LangGraph 对齐：[mcp-server/docs/langgraph-mcp-contract.md](../../mcp-server/docs/langgraph-mcp-contract.md)

## 终端 1 — multi-agent API

```powershell
Set-Location F:\view-agents\multi-agent
pip install -e .
ma-api
```

自检：`Invoke-RestMethod http://127.0.0.1:18082/health`

## 终端 2 — MCP HTTP Server

```powershell
Set-Location F:\view-agents\mcp-server
pip install -e .
$env:MULTI_AGENT_API_URL = "http://127.0.0.1:18082"
view-agents-mcp-http
```

默认：`http://127.0.0.1:8010/mcp`

## 终端 3 — agent-kit

```powershell
Set-Location F:\view-agents\agent-kit
pip install -e .
$env:MULTI_AGENT_API_URL = "http://127.0.0.1:18082"
$env:MCP_HTTP_URL = "http://127.0.0.1:8010/mcp"

agent-kit mcp-ping --live
agent-kit mcp-catalog --live
agent-kit refund-demo ORD-001 AS-001 --live
```

## 离线教学（无需 1/2）

```powershell
agent-kit mcp-catalog
agent-kit refund-demo ORD-001 AS-001
pytest -q
```

离线数据来自 `unified_socket.json` 与 Client stub，不含真实 Gateway 裁决。