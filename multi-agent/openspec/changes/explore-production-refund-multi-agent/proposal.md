# Proposal: multi-agent 可恢复执行协议（Python 仿真）

> **Status:** `propose` — 待评审后 `/opsx:apply`  
> **Change id:** `explore-production-refund-multi-agent`  
> **评审日期:** 2026-11-24

## 背景

`view-agents` 下已有 [`langgraph-agent`](../../../langgraph-agent)：**单图 ReAct + 内存状态**，适合演示「LLM 提议 → 调工具 → 循环」。  
生产 Multi-Agent（Supervisor 委派多 Worker）在 **外部写入**（退款、发券）时面临：响应丢失、重复投递、Worker 失联、晚到回写。

**线索场景：** 客服「退款后补发差价券」— 网关已受理退款，响应在回程丢失；Agent 只见超时。盲重试 → 第二笔退款；盲发券 → 无退款事实。

本项目在 **`multi-agent/`** 用 **Python 状态机 + SQLite + 全功能支付 Mock** 落实文章 11 张图（`docx/`）中的机制，并与 `langgraph-agent` 并行对照。

## 目标（全功能范围）

### P0 — 已规划且大部分已实现（MVP 核心）

| 能力 | 说明 |
|------|------|
| 执行协议 | Workflow / Task / Attempt / `business_key` 四层 |
| 状态机 | Workflow + Task 含 **UNKNOWN**；`state_machine.py` 约束转移 |
| Workers | `RefundWorker`、`CouponWorker` + `SupervisorEngine` |
| 裁决 | `ToolGateway` + `submit_proposal`（模型提议 / 系统裁决） |
| 持久化 | SQLite `Store`：task、tool_operation、outbox、audit |
| 租约与 fencing | `claim_task`、条件 UPDATE |
| Outbox 仿真 | 同事务写入 + `OutboxPipeline`（Kafka 语义） |
| 支付 Mock | FastAPI：幂等、查询、对账、故障注入、回调 |
| 测试 | `pytest` E2E + `T03_*` 六规则 + `fault_drill` 五场景 |

### P1 — propose 规划、apply 待完成

| 能力 | 对应图 |
|------|--------|
| NEEDS_REVIEW / 对账 / 人工收敛 API | 05、08 |
| Outbox 丢确认 / 崩溃 **专项 pytest**（接 drill） | 06 |
| Prometheus `/metrics` + 图 10 指标单测 | 10 |
| `docs/migration-phases.md` 四阶段 + feature 开关 | 11 |
| `demo_walkthrough`（Typer/脚本，对照 01–11） | 11 |
| 支付 Mock：额度 / 审批策略扩展、Webhook 文档对齐 | 03、09 |
| Gateway：额度配额单测（租户预算表或配置） | 09 |
| CI：`pytest` + `fault_drill` job | 12 |

### P2 — 对照与扩展（非 MVP 阻塞）

| 能力 | 说明 |
|------|------|
| `docker-compose`：Postgres + Redpanda/Kafka 与 SQLite 双写对照 | 06、10 |
| `deploy/k8s/` HPA 样板（ingest vs worker） | 01、10 |
| Go 服务骨架（与 Python 协议同 schema） | 远期 |
| HTTP Supervisor API（`POST /workflows`、`POST /proposals`） | 集成 |
| 可选 LLM 提议层对接 `langgraph-agent` | 互操作 |

### 硬约束

- **[slide-implementation-matrix.md](./slide-implementation-matrix.md)**：11 张图每节必有代码 + 验收；归档前全绿。
- **超时 ≠ 失败**；**business_key** 幂等；**UNKNOWN** 先追查再放行 DAG。

## Non-goals

- 不接入真实支付生产环境；语义对齐即可。
- 不把 Prompt 当幂等 / 授权 / 审计实现。
- 不做完整 SaaS 运营台、计费大盘。
- 不替换 `langgraph-agent`；文档互链、可选集成。
- P2 未完成不阻塞 MVP 归档（但矩阵 11 节必须满足）。

## 成功标准（归档）

1. `pip install -e ".[dev]" && pytest -q` 全绿（含 `fault_drill`、`T03_*`）。
2. `python scripts/fault_drill/run_all.py` 退出码 0。
3. `ma-demo timeout-reconcile` 演示主线；`demo_walkthrough` 覆盖 11 图检查点（P1）。
4. 矩阵文档逐节勾选；`tasks.md` P0+P1 与图 01–11 相关项完成。
5. `docs/payment-gateway-mock.md` 与实现 API 一致。

## 技术决策（propose 冻结）

| 决策 | 选择 |
|------|------|
| MVP 运行时 | **Python 3.10+**，可编辑安装 `multi-agent` |
| 状态真相 | **SQLite**（文件或 `:memory:`）；P2 可加 Postgres |
| 消息交接 | **Outbox + 进程内管道**；P2 接 Kafka |
| 支付 | **独立 FastAPI** `payment-mock` + `PaymentClient` |
| 测试 | **pytest**；图 11 用 `fault_drill` 模块 |

## 风险与假设

- 假设开发者环境可跑 Python / pip；Windows 友好（drill 用 Python 非 shell）。
- 支付 Mock 的 `504` 与真实网关行为需在联调时校准字段。
- 图 10「Kafka lag」在 P0 用指标占位 + 文档说明；P1 用可伪造 lag 的单测。

## 交付物清单

| 产物 | 路径 |
|------|------|
| 源码 | `src/multi_agent/**` |
| 支付网关 | `src/multi_agent/payment/server.py` |
| 测试 | `tests/**` |
| 故障演练 | `src/multi_agent/fault_drill/`、`scripts/fault_drill/` |
| 配图 | `docx/*.jpg` |
| 契约 | `slide-implementation-matrix.md` |
| 执行顺序 | `tasks.md` |
| 需求规格 | `specs.md` |
| 设计 | `design.md` |

## 关联 change

- 探索结论：[explore.md](./explore.md)
- 与 `langgraph-agent` OpenSpec 归档 change 独立；可在 `langgraph-agent` README 增加互链（P1）。

## 下一步

**`/opsx:apply`**：严格按 [tasks.md](./tasks.md) 章节顺序；仅勾选已完成项；P1 补齐后申请归档。