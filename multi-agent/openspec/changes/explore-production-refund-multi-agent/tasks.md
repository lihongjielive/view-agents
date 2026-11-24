# Tasks: 全功能实施计划（/opsx:apply）

> **提案:** [proposal.md](./proposal.md) · **规格:** [specs.md](./specs.md)  
> `[x]` = 已完成；`[ ]` = 待办（多为 P2）。

---

## P0 — MVP 核心（图 01–09）

### 0–2、4、7

- [x] 工程基建（pyproject、SQLite、Makefile、test.ps1、env.example）
- [x] 图 01–02 E2E + demo + k8s 样板
- [x] 图 04 business_key 测试

### 3. 图 03

- [x] Gateway + T03_* + 额度 `TENANT_QUOTA` + `test_gateway_gates.py`

### 5. 图 05

- [x] 状态机 + UNKNOWN + `test_state_machine.py`

### 6. 图 06

- [x] Outbox + `tests/test_outbox.py`

### 8. 图 08

- [x] NEEDS_REVIEW + reconciliation_queue + `test_figure08_needs_review.py`

### 9. 图 09

- [x] DAG + Gateway 表驱动（`test_gateway_gates.py`）

---

## P1 — 归档门禁

### 10. 图 10

- [x] metrics + docs + HPA

### 11. 图 11

- [x] fault_drill
- [x] `docs/migration-phases.md`
- [x] `ma-walkthrough` / `demo_walkthrough.py`

### 12. 文档与互操作

- [x] matrix pytest 对照（见 matrix 文末）
- [x] `langgraph-agent` README 互链
- [x] `scripts/ci.ps1` + `.github/workflows/ci.yml`
- [x] `ma-api` HTTP：`tests/test_http_api.py`
- [x] `demo_walkthrough` 11 步命令清单

---

## P2 — 可选

- [x] `docker-compose.yml` + profile `p2-kafka`
- [x] PostgreSQL Store 适配层（`postgres_store.py`、`store_factory.py`、`deploy/postgres/`）
- [x] Go `cmd/` 骨架 README
- [x] LangGraph 提议层 PoC（`langgraph_poc/`、`ma-langgraph-poc`、`.[langgraph]`）

---

## apply 约定

`pytest -q` + `python scripts/fault_drill/run_all.py` + `scripts/ci.ps1`