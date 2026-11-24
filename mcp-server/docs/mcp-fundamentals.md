# MCP 基础与 view-agents 对照（explore 教学摘录）

> 规范参考：[MCP Specification](https://modelcontextprotocol.io/specification/2026-07-28/basic)  
> 本节对应用户提供的「什么是 MCP」材料，并结合本 monorepo 落地。

## 1. 为什么需要 MCP（M×N → M+N）

**无 MCP：** 每对 (AI Host, 数据源) 各写一套胶水代码。3 个 Host × 3 个数据源 = **9 套**集成。

**有 MCP：** 中间协议统一「发现能力、调用工具、回注上下文」。每个数据源 **一个 Server**，每个 Host **一次 Client**，Notion/Vercel/自研 `ma-api` 均可复用。

```text
  Host (Cursor)          Host (Claude)          Host (自研)
       \                      |                      /
        \                     |                     /
         -------- MCP Client 层（各实现一次）--------
                          |
                    MCP 协议
                          |
         -------- Server 层（各数据源一次）--------
        /          |              \
  view-agents-mcp  vercel-mcp    notion-official
        |
   multi-agent ma-api（REST 真相源）
```

### 1.1 MCP vs Function Calling

| 层次 | 负责什么 |
|------|----------|
| **Function Calling** | 模型如何表达「我要调工具、参数是什么」 |
| **MCP** | 意图如何标准化到达外部系统（schema + 执行在 Server） |

**串联：** Host 将 `tools/list` 转成 FC schema → 模型出 `tool_calls` → Host 发 `tools/call` → Server 执行。

本仓库对照：

- `langgraph-agent`：`bind_tools` + `action` 节点 = **应用内 FC + 本地 invoke**
- `mcp-server`：把 `ma-api` 的 workflow/proposal **封装为 MCP tools**，Cursor 无需再写 HTTP 胶水

### 1.2 Agent / Skill / MCP / CLI

| 类比 | 本 monorepo 示例 |
|------|------------------|
| **Agent** | Cursor Agent、`langgraph-agent` ReAct 图 |
| **Skill** | `.cursor/skills`、`openspec /opsx:apply` 步骤 |
| **MCP** | `view-agents-mcp` → `multi_agent_submit_proposal` |
| **CLI** | `ma-demo figure-01`、`pytest`、`agent run` |

**典型组合（退款+券）：** Agent 分解任务 → Skill/OpenSpec 规定「先 proposal 后执行」→ MCP 取 workflow_id / Gateway 裁决 → CLI 跑 E2E 验证。

### 1.3 适用 vs 不适用

**适合 MCP（本项目的理由）：**

- 多 Host 共享同一套售后协议能力（Cursor + 未来自研客服 Copilot）
- 底层已有稳定 API（`ma-api`）且需分级授权、审计
- 模型参与决策，但 **执行** 必须在 multi-agent Worker

**不适合仅用 MCP、应直调 REST 的场景：**

- 定时对账脚本、纯 CI（直接 `pytest` / `curl ma-api`）
- 仅一个内置 LangGraph 且 tools 硬编码可满足（见 `langgraph_poc`）

---

## 2. 核心概念（一次工具调用）

### 2.1 三角色

- **Host**：Cursor（持有对话、策略、FC 转换）
- **Client**：Host 内建，与每个 MCP Server 一条连接
- **Server**：`view-agents-mcp`（FastMCP 进程）

### 2.2 两层架构

- **数据层：** JSON-RPC（`tools/list`、`tools/call`、`resources/read`、`prompts/get`…）
- **传输层：** 本仓库 **P0 = stdio**；**P2 = Streamable HTTP**（团队共享、OAuth）

### 2.3 三种原语（本项目规划）

| 原语 | 控制方 | view-agents 规划 |
|------|--------|------------------|
| **Tools** | 模型 | workflow / proposal / health（已实现桥接） |
| **Resources** | Host 注入上下文 | 执行协议摘要、`docx/03` 图说 URI |
| **Prompts** | 用户选模板 | 「售后退款+券助手」预组装消息 |

### 2.4 信任边界（退款域映射）

1. **Host 不信任 Server**：`destructiveHint` 仅提示；发券/退款执行必须经 Gateway + Worker，Host 仍要确认。  
2. **Server 不信任 Client**：校验 `tenant`、`access_token`、参数范围；禁止 MCP 直写支付。  
3. **反向能力**（Sampling/Elicitation）：P2 若启用，Host 可拒绝；MCP 不得绕过用户选环境。

### 2.5 Tool Annotations（Hint，非安全策略）

查询类：`readOnlyHint=true`、`idempotentHint=true`  
写侧缘（建 workflow）：`destructiveHint=false` 但仍可能创建持久状态 — Host **不应**因 hint 跳过确认。

---

## 3. 本地 stdio vs 远程 HTTP

| 模式 | 适用 |
|------|------|
| **stdio** | 开发者本机、密钥走 env、与 Cursor 子进程同生命周期 |
| **Streamable HTTP** | 团队统一 URL、OAuth 2.1、Vercel 式多 Host 接入 |

**stdio 纪律：** 协议走 stdout；**日志只用 stderr**（`print` 到 stdout 会破坏 JSON-RPC 行）。

---

## 4. 与本 monorepo 三项目关系

详见 [`../openspec/changes/explore-mcp-bridge/explore.md`](../openspec/changes/explore-mcp-bridge/explore.md) 与 [`usage-scenarios.md`](../openspec/changes/explore-mcp-bridge/usage-scenarios.md)。