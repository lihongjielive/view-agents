# 十一图 × 实现保证矩阵

> **契约：** 本 change 在 **归档前** 必须满足下表每一行的「验收方式」；缺一项视为未完成。  
> 配图路径：`docx/0N-*.jpg`

## 总原则

1. **可运行**：`pip install -e ".[dev]" && pytest` + `ma-demo timeout-reconcile`；远期可加 `docker compose` 对照 Kafka/PG。  
2. **可观测**：Prometheus 指标或结构化日志覆盖 10 图所列监控项（MVP 可用 `/metrics` + 集成测试断言）。  
3. **可演示**：`scripts/demo_walkthrough.sh` 按 01→11 图顺序旁白对应 API/SQL 检查点。

---

## 01 · 可恢复执行协议总览

| 能力 | 实现组件 | 验收 |
|------|----------|------|
| Supervisor 委派退款/发券两 Task | `cmd/supervisor` | E2E：创建 workflow，两条 task 入库 |
| 支付受理但响应丢失 | `cmd/payment-mock` `DropResponse` | 注入后 refund task → UNKNOWN |
| 发券等待依赖 | DAG 依赖门 | coupon 在 refund 未 SUCCEEDED 时保持 WAITING |
| 技术栈落地 | Compose + `deploy/k8s/` 清单 | `kubectl apply --dry-run=client` 通过；Compose 健康检查绿 |

**图：** `01-execution-protocol-overview.jpg`

---

## 02 · 网关已成功、Agent 只见超时

| 能力 | 实现 | 验收 |
|------|------|------|
| POST 受理成功、响应丢弃 | payment-mock 模式 | 单测：mock 内部 refund 记录为 succeeded，客户端得 timeout |
| 禁止把超时当失败重试 POST | refund-worker + gateway | 集成：超时后无第二次 POST（计数器=1） |
| 依赖门挡住发券 | supervisor DAG | 集成：coupon 仍 WAITING |

**图：** `02-refund-response-lost-timeout.jpg`

---

## 03 · 模型提建议，系统做裁决

| 能力 | 实现 | 验收 |
|------|------|------|
| Agent 仅提交「候选动作」API | `POST /proposals` | 不直接写支付表 |
| 工作流态 / 权限 / 业务事实 / Gateway | `internal/gateway` 策略链 | 表驱动单测 ≥6 条（含拒绝路径） |
| 六条生产规则 | gateway + workflow | 见下表子项集成测试 |

| 规则 | 实现点 | 测试 id |
|------|--------|---------|
| 业务键归并 | `tool_operations.business_key` UNIQUE | `T03_merge` |
| 旧 Worker 禁回写 | fencing UPDATE | `T03_fence` |
| 依赖满足才执行 | DAG READY 转换 | `T03_dep` |
| 补偿期禁新写 | workflow=COMPENSATING 拒写 | `T03_comp` |
| 未知结果可追查 | UNKNOWN + 查询 API | `T03_trace` |
| 工具调用再授权 | Gateway 审计日志 `audit_log` 表 | `T03_audit` |

**图：** `03-model-proposes-system-decides.jpg`

---

## 04 · 幂等键是 business_key，不是 task_id

| 能力 | 实现 | 验收 |
|------|------|------|
| 四层标识字段 | migrations + domain 类型 | schema 测试 |
| 重试 attempt++，business_key 不变 | refund-worker | 同一 task 两次 attempt，gateway 只一笔业务退款 |
| 键格式 | `tenant|tool|order|aftersale` | 单测解析与生成 |

**图：** `04-business-key-not-task-id.jpg`

---

## 05 · UNKNOWN 为正式状态

| 能力 | 实现 | 验收 |
|------|------|------|
| Workflow 状态机 | `internal/workflow` | 单测全转移 |
| Task 状态机含 UNKNOWN | 同上 + DB CHECK | 单测：RUNNING→UNKNOWN→SUCCEEDED |
| UNKNOWN 收敛路径 | reconcile worker | 远端查询 / 对账表 / 人工 API 三入口 |
| 租约字段 | `owner, lease_until, row_version` | 领取/续期/过期单测 |

**图：** `05-unknown-formal-state.jpg`

---

## 06 · Task 与 Outbox 同事务提交

| 能力 | 实现 | 验收 |
|------|------|------|
| 同事务写 task + outbox | repository Tx | 集成：提交失败则二者皆无 |
| Outbox Publisher | `cmd/outbox-publisher` | 发布确认丢失重发：事件至少一次、任务不丢 |
| Ingest → 队列表 | `cmd/ingest-consumer` | Offset 前崩溃重放：READY 任务数不增脏数据 |
| 唯一逻辑任务 | consumer 幂等 `idempotency_key` | 重复消息消费 2 次仅 1 条执行 |

**图：** `06-outbox-task-and-event.jpg`

---

## 07 · 租约与 fencing

| 能力 | 实现 | 验收 |
|------|------|------|
| 租约过期再领取 | `internal/lease` | 集成：A 失联后 B `attempt_no=2` |
| 条件 UPDATE fencing | `internal/fencing` | A 晚到 `attempt=1` 更新 0 行 |
| B 成功提交 | 同上 | B `attempt=2` 更新 1 行 |

**图：** `07-lease-fencing-old-worker.jpg`

---

## 08 · 退款超时：先查询再决定

| 能力 | 实现 | 验收 |
|------|------|------|
| 先持久化 PENDING | refund-worker 顺序 | SQL 断言先于 HTTP |
| 超时标 UNKNOWN | worker | 非 FAILED |
| 按 business_key GET | payment client | CONFIRMED → task SUCCEEDED |
| 无法查询 → 对账/人工 | `NEEDS_REVIEW` + API | 禁止第三次 POST refund |

**图：** `08-refund-timeout-query-first.jpg`

---

## 09 · 发券前两道门

| 能力 | 实现 | 验收 |
|------|------|------|
| DAG 门：SUCCEEDED+版本有效 | supervisor | UNKNOWN 下游仍 WAITING |
| DAG 门：FAILED/无效版本 | supervisor | 不发 READY |
| Gateway 门：身份/租户/额度/审批/令牌/流程态 | gateway 策略 | 表驱动测试 ≥6 项 |
| 全过 → 下游再校验 | coupon-worker | E2E 发券成功 |

**图：** `09-dag-and-tool-gateway-gates.jpg`

---

## 10 · Kafka lag 与任务积压分离

| 能力 | 实现 | 验收 |
|------|------|------|
| 指标：kafka_consumer_lag | ingest metrics | 集成测试可 scrape 或日志断言 |
| 指标：task_ready_oldest_age_seconds | supervisor metrics | 造积压后 age>0 |
| 指标：task_ready_pending_count | SQL + gauge | 同上 |
| UNKNOWN 计数、租约续期失败率、补偿积压、P95、token/task | `internal/metrics` | 文档列名与 `/metrics` 存在；E2E 至少各 1 个非零场景 |
| 交接/执行拆分部署 | compose 多副本注释 + HPA 样例 | k8s HPA 两条（ingest / worker） |

**图：** `10-kafka-lag-vs-task-backlog.jpg`

---

## 11 · 渐进迁移与故障演练

| 能力 | 实现 | 验收 |
|------|------|------|
| 四阶段 feature 开关 | `config` 分阶段启用 | `docs/migration-phases.md` + 每阶段 compose profile |
| 五步故障注入 | `scripts/fault_drill/*.sh` | CI job `fault-drill` 全绿 |

| 注入场景 | 脚本 |
|----------|------|
| 发布确认丢失 | `lost_publish_ack.sh` |
| Offset 前崩溃 | `crash_before_offset.sh` |
| Worker 失联 | `worker_disconnect.sh` |
| 成功响应丢失 | `success_response_lost.sh` |
| 迟到回调 | `late_callback.sh` |

**图：** `11-migration-four-steps.jpg`

---

## 归档门禁（Definition of Done）

```text
[x] 11 节均有 pytest 用例（见下表 pytest node 列）
[x] pytest -q && scripts/fault_drill/run_all.py
[x] ma-walkthrough 与 docx/01–11 一致
[ ] proposal P2 项（非阻塞）
```

### pytest 对照（查漏）

| 图 | pytest |
|----|--------|
| 01 | `tests/test_figure01_skeleton.py` |
| 02 | `tests/test_figure02_response_lost.py` |
| 03 | `tests/test_gateway_t03.py` |
| 04 | `tests/test_figure04_business_key.py` |
| 05 | `tests/test_state_machine.py` |
| 06 | `tests/test_outbox.py` |
| 07 | `tests/test_fencing.py` + `fault_drill.worker_disconnect` |
| 08 | `tests/test_figure08_needs_review.py` |
| 09 | `tests/test_gateway_gates.py` |
| 10 | `tests/test_metrics.py` |
| 11 | `tests/test_fault_drill.py` |