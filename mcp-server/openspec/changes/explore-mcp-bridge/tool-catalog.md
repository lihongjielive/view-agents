# MCP Tool Catalog（含 Annotations 规划）

## 注解约定

| Tool | readOnlyHint | destructiveHint | idempotentHint | 备注 |
|------|--------------|-----------------|----------------|------|
| `mcp_ping` | true | false | true | |
| `mcp_server_info` | true | false | true | |
| `multi_agent_health` | true | false | true | 探测 |
| `multi_agent_create_workflow` | false | false | false | 创建持久 workflow |
| `multi_agent_submit_proposal` | true | false | true | **无副作用** 裁决 |
| `langgraph_agent_status` | true | false | true | 占位 |

> Annotations 为 **Hint**；Host 安全策略独立。

---

## `mcp_ping`

- **Returns:** `{ "ok": true, "service": "view-agents-mcp", "version": "…" }`

## `mcp_server_info`

- **Returns:** enabled bridges（脱敏）、version

## `multi_agent_health`

| 参数 | 类型 | 必填 |
|------|------|------|
| `base_url` | string | 否 |

## `multi_agent_create_workflow`

| 参数 | 类型 | 必填 |
|------|------|------|
| `order_id` | string | 是 |
| `after_sale_id` | string | 是 |
| `refund_amount` | number | 是 |
| `tenant` | string | 否 |
| `base_url` | string | 否 |

## `multi_agent_submit_proposal`

| 参数 | 类型 | 必填 |
|------|------|------|
| `workflow_id` | string | 是 |
| `tool` | string | 是 | `refund.create` \| `coupon.issue` |
| `order_id` | string | 是 |
| `after_sale_id` | string | 是 |
| `amount` | number | 是 |
| `tenant` / `actor` / `access_token` / `base_url` | | 否 |

## Resources（P0 explore）

| URI | MIME | 内容 |
|-----|------|------|
| `view-agents://protocol/execution-summary` | text/markdown | 四层身份、提议 vs 执行 |
| `view-agents://multi-agent/gateway-codes` | text/markdown | T03 代码表 |

## Prompts（P0 explore）

| name | 用途 |
|------|------|
| `refund-after-sale-assist` | 售后退款+券：先 workflow → proposal，禁止直写支付 |