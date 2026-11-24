# 渐进迁移四阶段（图 11）

| 阶段 | 能力 | 本仓库开关 / 验证 |
|------|------|-------------------|
| **1** | 稳定 business_key + Gateway 只读查询 | `payment-mock` GET；`pytest tests/test_figure04_*` |
| **2** | Task 持久化 + 租约 + Outbox | SQLite `Store`；`tests/test_outbox.py` |
| **3** | Kafka 交接与 Worker 分离 | `OutboxPipeline`；可选 `docker compose --profile p2-kafka` |
| **4** | DAG + 并发预算 | `ToolGateway` TENANT_QUOTA；HPA 样板 `deploy/k8s/` |

环境变量（示意）：

```bash
MULTI_AGENT_PHASE=2   # 1–4，默认 2（当前仿真）
```

执行 `ma-walkthrough` 查看逐步命令。