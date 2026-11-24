# Gateway 裁决代码（T03 摘要）

| code | 含义 |
|------|------|
| OK | 允许 |
| T03_MERGE | business_key 合并幂等 |
| T03_DEP | 发券依赖退款未完成 |
| T03_QUOTA | 超额 |
| T03_REVIEW | 工作流 NEEDS_REVIEW |
| T03_COMP | 补偿窗口禁止新写 |
| T09_TOKEN | token 无效 |
| WF404 | workflow 不存在 |

MCP 调用 proposal 后应把 `code` 回显给用户，再决定是否触发 Worker（非 MCP 职责）。