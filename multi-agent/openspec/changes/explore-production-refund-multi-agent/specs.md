# Specs: 功能需求（按图 + 模块）

> 可测试陈述；验收见 [slide-implementation-matrix.md](./slide-implementation-matrix.md) 与 `tests/`。

## SUP — Supervisor

| ID | 需求 |
|----|------|
| SUP-1 | 创建 workflow 时写入 **refund**（READY）与 **coupon**（WAITING，依赖 refund）两条 task |
| SUP-2 | refund **SUCCEEDED** 且 `result_version≥1` 时，coupon 可转为 READY（Outbox `task.ready`） |
| SUP-3 | refund **UNKNOWN/FAILED** 时 coupon 保持 WAITING |
| SUP-4 | 工作流状态支持 COMPENSATING 时 Gateway 拒新写（T03_COMP） |

## TASK — Task 状态机

| ID | 需求 |
|----|------|
| TASK-1 | 状态集含 WAITING, READY, CLAIMED, RUNNING, SUCCEEDED, FAILED, **UNKNOWN** |
| TASK-2 | 非法转移抛错或 SQL 条件更新失败 |
| TASK-3 | `claim_task` 递增 `attempt_no`；`business_key` 在 task 生命周期内不变 |
| TASK-4 | `fenced_task_update` 校验 owner + attempt + row_version + lease |

## TOOL — Tool operation

| ID | 需求 |
|----|------|
| TOOL-1 | 外呼前写入 `tool_operations`，初始 **PENDING** |
| TOOL-2 | HTTP 超时 → **UNKNOWN**（非 FAILED） |
| TOOL-3 | GET 远端确认 → **CONFIRMED** + task SUCCEEDED |
| TOOL-4 | `business_key` 表级 UNIQUE |

## GW — Tool Gateway

| ID | 需求 |
|----|------|
| GW-1 | `submit_proposal` 不调用支付、不改 task（仅裁决） |
| GW-2 | 六规则：MERGE, FENCE(协作 store), DEP, COMP, TRACE(协作 worker), AUDIT |
| GW-3 | 每次 `evaluate` 写 `audit_log`（含拒绝） |
| GW-4 | 发券前校验 refund SUCCEEDED（DEP） |

## PAY — 支付 Mock

| ID | 需求 |
|----|------|
| PAY-1 | POST `/v1/refunds` 幂等（同 business_key 返回同退款） |
| PAY-2 | GET `/v1/refunds/{business_key}` 查询 |
| PAY-3 | POST `/v1/reconciliation/by-keys` 批量对账 |
| PAY-4 | 故障：`drop_response_after_success`, `timeout`, `slow`, `fail_business`, `late_callback` |
| PAY-5 | `/v1/admin/fault-injection`、`/v1/admin/metrics`、`/v1/admin/callbacks` |
| PAY-6 | `drop` / `late_callback`：服务端已成功写入，客户端得 504 |

## OUT — Outbox

| ID | 需求 |
|----|------|
| OUT-1 | workflow 创建与 task.ready 与 outbox **同事务** |
| OUT-2 | Publisher 可模拟「确认丢失」后重发 |
| OUT-3 | Consumer `consume_event_idempotent` 防重放重复副作用 |

## WRK — Workers

| ID | 需求 |
|----|------|
| WRK-1 | RefundWorker：Gateway → PENDING → POST → ok/unknown/fail |
| WRK-2 | 超时后不自动第二次 POST；须 `reconcile` GET |
| WRK-3 | CouponWorker 仅在 Gateway 允许时发券 |

## OBS — 可观测性（P1）

| ID | 需求 |
|----|------|
| OBS-1 | 暴露 `unknown_operations_count`、`task_ready_pending_count` 等 |
| OBS-2 | 文档区分 Kafka lag vs READY oldest age |

## DRILL — 故障演练（图 11）

| ID | 需求 |
|----|------|
| DRILL-1..5 | `lost_publish_ack`, `crash_before_offset`, `worker_disconnect`, `success_response_lost`, `late_callback` |
| DRILL-6 | `pytest -m fault_drill` 与 `run_all.py` 等价 |

## DOC — 演示与迁移（P1）

| ID | 需求 |
|----|------|
| DOC-1 | `migration-phases.md` 四步与文图 11 一致 |
| DOC-2 | walkthrough 每步引用 `docx/0N-*.jpg` |