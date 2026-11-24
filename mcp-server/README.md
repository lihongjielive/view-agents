# view-agents-mcp

**并列第三项目**：通用 [MCP](https://modelcontextprotocol.io/) Server（**FastMCP + stdio**），与 `langgraph-agent`、`multi-agent` **弱耦合**。

## 统一插口（USB-C）

- **契约：** [`contracts/unified_socket.json`](contracts/unified_socket.json)（`tools/list` 标签 = LangGraph tool 名 = `ma-api` 映射）
- **按需标签：** 先 `mcp_tools_catalog`（短目录）→ `mcp_tools_describe`（完整 schema）
- **Resource：** `view-agents://socket/manifest` 供 Host 校验版本

| 问卷选型 | 说明 |
|----------|------|
| 角色 | 通用骨架；可选 HTTP 接 `ma-api` |
| 运行时 | Python + FastMCP |
| 安全 | 仅有 workflow / proposal tools，**无支付直写** |

探索文档：

- [`openspec/changes/explore-mcp-bridge/explore.md`](openspec/changes/explore-mcp-bridge/explore.md) — 架构、原语、安全  
- [`docs/mcp-fundamentals.md`](docs/mcp-fundamentals.md) — MCP 教学 + view-agents 对照  
- [`openspec/changes/explore-mcp-bridge/usage-scenarios.md`](openspec/changes/explore-mcp-bridge/usage-scenarios.md) — 七种使用经验

## 安装

```bash
cd mcp-server
pip install -e .
```

## 运行（stdio）

```bash
view-agents-mcp
# 或
python -m view_agents_mcp.server
```

## 运行（Streamable HTTP · P1）

```bash
view-agents-mcp-http
# 默认 http://0.0.0.0:8010/mcp
```

环境变量见 `env.example`（`FASTMCP_HOST` / `FASTMCP_PORT`）。可选 `MCP_HTTP_BEARER_TOKEN` 启用 Bearer（仅 HTTP）。鉴权路线图见 [`docs/oauth-roadmap.md`](docs/oauth-roadmap.md)。

## CI

```bash
pytest -q
# Windows: scripts/ci.ps1
# Monorepo: .github/workflows/view-agents-ci.yml
```

## 可选：桥接 multi-agent

```bash
# 终端 1
cd ../multi-agent && ma-api

# 终端 2
set MULTI_AGENT_API_URL=http://127.0.0.1:18082
view-agents-mcp
```

## Cursor `mcp.json` 示例

```json
{
  "mcpServers": {
    "view-agents": {
      "command": "view-agents-mcp",
      "args": [],
      "env": {
        "MULTI_AGENT_API_URL": "http://127.0.0.1:18082"
      }
    }
  }
}
```

复制 `env.example` 为本地 `.env` 时勿提交仓库。

## Tools 一览

见 [tool-catalog.md](openspec/changes/explore-mcp-bridge/tool-catalog.md)。

## 待补全

用户在问卷中选择了 **等待「要求是：」原文**。补全后执行 `/opsx:propose` 细化 P0/P1 任务。