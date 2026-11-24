# OAuth 与 HTTP 鉴权路线图（MCP P1）

> 对齐用户材料：Vercel MCP 的 **统一 URL + OAuth 2.1 + scope 裁剪**；本仓库分阶段落地。

## Phase 0 — 开发 Bearer（P1 已实现）

| 项 | 说明 |
|----|------|
| 场景 | 本机 `view-agents-mcp-http`，小团队共享 |
| 配置 | `MCP_HTTP_BEARER_TOKEN`（可选） |
| 行为 | 未设置：仅监听 `FASTMCP_HOST`，文档警告勿暴露公网 |
| 校验 | HTTP 层比对 `Authorization: Bearer` |

**不等于** multi-agent Gateway token；两层分离：

- **MCP 层**：谁可以连上 MCP Server  
- **ma-api 层**：`MULTI_AGENT_ACCESS_TOKEN` → Gateway `T09_TOKEN`

## Phase 1 — 静态 API Key 轮换

- 密钥由运维注入 K8s Secret / Cursor 团队配置  
- 支持 `MCP_HTTP_BEARER_TOKEN` 与 `MCP_HTTP_BEARER_TOKEN_PREVIOUS` 双钥轮换  
- 审计：stderr 结构化日志（request_id、tool_name，无 body PII）

## Phase 2 — OAuth 2.1（设计冻结，P2 实现）

参考 MCP 远程部署与 Vercel 文档：

1. 首次 `401` + `WWW-Authenticate` 含 authorization server 元数据  
2. Host 引导用户授权，获取 access token  
3. **Scope → tools/list 裁剪**（例：`proposal:read` 无 `create_workflow`）  
4. 无状态 HTTP；`workflow_id` 由 Client 每次传递

| Scope 示例 | 可见 tools |
|------------|------------|
| `mcp:ping` | `mcp_ping`, `mcp_server_info` |
| `ma:read` | + `multi_agent_health` |
| `ma:propose` | + `submit_proposal` |
| `ma:workflow` | + `create_workflow` |

## Phase 3 — 企业 IdP

- OIDC 联合、租户维度与 `TENANT_QUOTA` 对齐  
- 破坏性 tool 强制 Host 确认（不信任 `destructiveHint`）

## 与 FastMCP 的关系

- P1：自定义 Starlette 中间件或 `FastMCP` 前置校验  
- P2：评估 `FastMCP.auth` 与官方 OAuth 示例（随 SDK 升级）

## 检查清单（评审）

- [x] Phase 0 实现与文档一致（`http_bearer.py` + `test_http_bearer.py`）  
- [ ] 未将 OAuth 未完成标为「已生产」  
- [ ] MCP token 与 `ma-api` token 文档分章说明