# MCP 使用经验（view-agents）

> 覆盖 Host 配置、与 langgraph / multi-agent 组合、调试与踩坑。

## 场景 A — 纯连通（零 HTTP）

**谁：** 新同学验证 MCP 进程能被 Cursor 拉起。

1. `pip install -e mcp-server`
2. Cursor `mcp.json`：`command: view-agents-mcp`
3. 对话：「调用 mcp_ping」

**预期：** `ok: true`；`mcp_server_info` 显示 `multi_agent_api_configured: false`。

**经验：** 未配 `MULTI_AGENT_API_URL` 时，业务 tools 返回结构化 `error`，不会伪造成功。

---

## 场景 B — Cursor + ma-api（提议层闭环）

**谁：** 产品经理 / 客服助手在 IDE 里演练「系统裁决」。

1. 终端：`cd multi-agent && ma-api`
2. `mcp.json` env：`MULTI_AGENT_API_URL=http://127.0.0.1:18082`
3. 模型编排：
   - `multi_agent_create_workflow(order_id=…, after_sale_id=…, refund_amount=…) `
   - `multi_agent_submit_proposal(workflow_id=…, tool=refund.create, …)`
   - 再 `tool=coupon.issue`（应得 `T03_DEP` 若退款未执行）

**预期：** proposal 仅返回 `allow/code/reason`；**不会出现** `payment.post_refund` audit（执行在 Worker，非 MCP）。

**经验：** 与 docx **图 03** 一致：MCP = 模型触达的提议入口，不是支付客户端。

---

## 场景 C — LangGraph FC vs MCP（同一业务两种 Host）

| 路径 | 模型上下文 | 工具执行 |
|------|------------|----------|
| `langgraph-agent` | `messages` + ToolMessage | Python `@tool` 同步 invoke |
| Cursor + MCP | Chat + MCP tool results | `view-agents-mcp` → HTTP |

**对齐方式：** LangGraph 的 tool 实现应调用 `POST /v1/proposals`（或未来调 MCP Client），与 MCP Server 桥接 **同一 REST**。

**经验：** ReAct 环在 LangGraph 图内闭合；MCP 在 **Host 外** 闭合——二者可并存，不要 duplicate 支付逻辑。

---

## 场景 D — Skill + MCP + CLI（归档门禁）

**谁：** 开发按 OpenSpec 交付图 01–11。

1. **Skill / tasks.md** 列出 `pytest -q`、`ma-walkthrough`
2. **MCP** 可选：`multi_agent_health` 做环境探测
3. **CLI** 真跑：`ma-demo figure-01`、`python scripts/fault_drill/run_all.py`

**经验：** 固定流程用 Skill/文档；动态探测用 MCP；批量验证用 CLI/pytest。MCP **不替代** CI。

---

## 场景 E — Resource 注入（Host 拉上下文）

Host 在对话前 `resources/read`：

- URI：`view-agents://protocol/execution-summary` — 四层身份、business_key、提议 vs 执行
- URI：`view-agents://multi-agent/gateway-codes` — T03_* 代码表

**经验：** 减轻模型 hallucinate Gateway 规则；与 Tools 解耦（Resources 非模型主动调）。

---

## 场景 F — Prompt 模板（用户斜杠命令）

用户选 `refund-after-sale-assist`：

- 预组装：必须先 `create_workflow` → `submit_proposal` → 禁止直接退款 POST 的 checklist

**经验：** 领域规范固化在 Server，换 Host 仍一致。

---

## 场景 G — P2 远程 MCP（规划）

团队部署 `https://mcp.example.com/view-agents`：

- OAuth scope 裁剪 `tools/list`（只读角色不见 `create_workflow`）
- 破坏性隔离：写操作单独 tool + Host 确认

参考用户材料中的 **Vercel MCP**：统一 URL、集中凭证、scope 裁剪。

---

## 踩坑清单

| 现象 | 原因 | 处理 |
|------|------|------|
| MCP 突然断连 | stdio 上 `print` 调试 | 改 `logging` → stderr |
| 工具描述不准，模型乱调 | description 过于简略 | 写清前置条件、返回字段 |
| proposal 总被拒 | token/tenant/依赖 | 读 `code`，先 refund 再 coupon |
| 以为 MCP 已退款 | 混淆提议与执行 | 查 Store/Worker 或跑 `ma-demo` |

---

## 调试命令

```bash
# 仅测桥接（需 ma-api）
curl http://127.0.0.1:18082/health

# MCP 离线单测
cd mcp-server && pytest -q
```