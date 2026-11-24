# 执行协议摘要（供 MCP Resource 注入）

## 四层身份

| 层级 | 标识 | 语义 |
|------|------|------|
| Workflow | `workflow_id` | 一次售后工单 |
| Task | `task_id` + `logical_step_key` | refund / coupon DAG |
| Attempt | `attempt_no` | 租约重领递增 |
| Tool operation | `business_key` | 外部幂等键 |

## 提议 vs 执行

- **提议：** `submit_proposal` / MCP `multi_agent_submit_proposal` → Gateway 只裁决
- **执行：** Worker + 支付 Mock；MCP **不得** POST `/v1/refunds`

## UNKNOWN

响应丢失 → Task `UNKNOWN` → 查询/对账，禁止盲重试 POST。

详见 `multi-agent/docx/` 图 01–11。