# Go 服务骨架（P2 / 远期）

Python MVP 已用 SQLite `Store` + 进程内 Worker 落实十一图机制。Go 目录用于 **同协议、同表结构** 的进程拆分对照，不阻塞 Python 归档。

## 建议目录（未实现）

```text
cmd/go/
  supervisor/     # HTTP：workflow / proposal / health
  worker-refund/
  worker-coupon/
  ingest/         # Outbox → Kafka（profile p2-kafka）
internal/
  store/          # PostgreSQL，与 deploy/postgres/schema.sql 一致
  gateway/        # ToolGateway 六规则（MERGE, FENCE, …）
  payment/        # 支付客户端 + business_key 幂等
```

## 与 Python 的边界

| 层 | Python（本仓 MVP） | Go（远期） |
|----|-------------------|------------|
| 提议 | LangGraph PoC、`submit_proposal` | 同 REST `/v1/proposals` |
| 真相 | `Store` / `PostgresStore` | `internal/store` |
| Worker | `workers/refund.py` | 独立 Deployment + 租约 |
| 观测 | `metrics.py`、HPA 样板 | Prometheus 同名指标 |

## 环境

- PostgreSQL：`docker compose --profile p2-postgres up -d`
- `MULTI_AGENT_STORE_URL=postgresql://multi:multi@localhost:5432/multi_agent`

## 起步验证（Python 侧）

```bash
pip install -e ".[dev,postgres]"
export MULTI_AGENT_POSTGRES_DSN=postgresql://multi:multi@localhost:5432/multi_agent
pytest tests/test_postgres_store.py -q
```

Go 实现时以 `openspec/changes/explore-production-refund-multi-agent/specs.md` 与 `design.md` 为契约源。