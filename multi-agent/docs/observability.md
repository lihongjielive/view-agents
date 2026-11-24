# 可观测性（图 10）

## 核心原则

**Kafka consumer lag 低 ≠ 执行侧无积压。**  
交接侧看 **outbox 未发布条数**（本仿真 `multi_agent_kafka_consumer_lag`）；执行侧看 **READY 任务数 / 最老 READY 年龄**。

| 指标 | 含义 | 扩容对象 |
|------|------|----------|
| `multi_agent_kafka_consumer_lag` | 未发布 Outbox 条数 | Ingest / Publisher |
| `multi_agent_outbox_unpublished_count` | 同上 | Publisher |
| `multi_agent_task_ready_pending_count` | 待执行 READY 任务 | Refund/Coupon Worker |
| `multi_agent_task_ready_oldest_age_seconds` | 最老 READY 等待秒数 | Worker |
| `multi_agent_unknown_operations_count` | 待追查 UNKNOWN 工具操作 | Reconcile job |
| `multi_agent_compensation_workflow_count` | COMPENSATING 工作流 | 人工 / 补偿 |
| `multi_agent_lease_renew_failure_total` | 租约续期失败累计 | Worker 健康 |

## 抓取方式

```bash
pip install -e .
ma-metrics          # http://0.0.0.0:18081/metrics
```

默认读 `:memory:`；文件库：

```bash
set MULTI_AGENT_STORE_PATH=multi_agent.db
ma-metrics
```

## 代码

- 聚合：`MetricsCollector.collect()`
- HTTP：`multi_agent.metrics_server`
- 测试：`pytest -m metrics`