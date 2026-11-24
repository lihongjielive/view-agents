# multi-agent

与 [`langgraph-agent`](../langgraph-agent) 平行的 **生产级 Multi-Agent** 探索工程：把「Supervisor 委派任务」落实为 **可恢复、可确认、可审计** 的执行协议，而不是仅靠 LLM 重试。

## 业务叙事（线索场景）

客服诉求：**退款后补发差价券**。Supervisor 将 **退款** 与 **发券** 交给两个 Agent：

1. 退款请求已被支付网关受理，但 **成功响应在返回途中丢失**；
2. Worker 侧仅见 **HTTP 超时** → 若盲重试可能 **第二笔退款**；若直接发券则 **缺少可信退款事实**。

核心原则（见文图 `docx/`）：

- **超时 ≠ 失败**；无远端事实时，不能把超时改写成失败。
- **模型提建议，系统做裁决**（幂等、授权、审计不由 Prompt 承担）。
- **UNKNOWN 必须是正式状态**；确认后再放行 DAG 下游（发券）。

## 与 langgraph-agent 的定位对比

| 维度 | langgraph-agent | multi-agent（本项目） |
|------|-----------------|------------------------|
| 运行时 | Python + LangGraph 单图 ReAct | **Python 状态机仿真** + SQLite + 全功能支付 Mock |
| 状态 | 进程内 MemorySaver / messages | PostgreSQL Task 状态机 + 租约 |
| 委派 | 单 Agent 工具循环 | Supervisor + 多 Worker + DAG 依赖门 |
| 外部写入 | Mock `@tool` | Tool Gateway + **business_key** 幂等 |
| 故障 | 演示级 | Outbox、Kafka、fencing、UNKNOWN 追查 |

## 配图目录

文章 11 张图位于 **`docx/`**（与幻灯片顺序一致）：

| 文件 | 主题 |
|------|------|
| `01-execution-protocol-overview.jpg` | 可恢复执行协议总览 |
| `02-refund-response-lost-timeout.jpg` | 网关已成功、Agent 只见超时 |
| `03-model-proposes-system-decides.jpg` | 模型提建议、系统做裁决 |
| `04-business-key-not-task-id.jpg` | 幂等键是 business_key 非 task_id |
| `05-unknown-formal-state.jpg` | Workflow / Task 状态机 |
| `06-outbox-task-and-event.jpg` | 任务与 Outbox 同事务提交 |
| `07-lease-fencing-old-worker.jpg` | 租约 + attempt fencing |
| `08-refund-timeout-query-first.jpg` | 超时先查询再决定 |
| `09-dag-and-tool-gateway-gates.jpg` | 发券前两道门 |
| `10-kafka-lag-vs-task-backlog.jpg` | 交接侧与执行侧分别扩容 |
| `11-migration-four-steps.jpg` | 渐进迁移与故障演练 |

## 文档（OpenSpec · propose）

- [**提案 proposal**](openspec/changes/explore-production-refund-multi-agent/proposal.md) — P0/P1/P2 全功能范围
- [**规格 specs**](openspec/changes/explore-production-refund-multi-agent/specs.md)
- [**设计 design**](openspec/changes/explore-production-refund-multi-agent/design.md)
- [**任务 tasks**](openspec/changes/explore-production-refund-multi-agent/tasks.md) — `/opsx:apply` 顺序
- [探索 explore](openspec/changes/explore-production-refund-multi-agent/explore.md)
- [**十一图实现矩阵（验收契约）**](openspec/changes/explore-production-refund-multi-agent/slide-implementation-matrix.md)
- [任务清单](openspec/changes/explore-production-refund-multi-agent/tasks.md)

## 快速开始（Python 仿真）

```bash
cd F:\view-agents\multi-agent
pip install -e ".[dev]"
# 或：make install && make test
.\scripts\test.ps1          # Windows
.\scripts\test.ps1 -FaultDrill
pytest -q
pytest -m figure01
pytest -m figure02
pytest -m metrics
ma-metrics            # :18081/metrics
ma-demo figure-02
pytest -m fault_drill   # 图 11 五类故障演练
python scripts/fault_drill/run_all.py
pytest tests/test_gateway_t03.py  # 图 03 六规则 T03_*
ma-demo figure-01
ma-demo happy
ma-demo timeout-reconcile
payment-mock   # 可选：独立网关 http://0.0.0.0:18080
```

支付 Mock API：[docs/payment-gateway-mock.md](docs/payment-gateway-mock.md)

远期对照栈：Go · PostgreSQL · Kafka · K8s（见 `design.md`）；**MVP 以 Python 达标十一图机制为准**。

## 实现承诺

**11 张 `docx/` 配图中的技术点必须全部可运行、可验收**，不得缩减机制（支付可用 mock，语义须一致）。

验收契约：[slide-implementation-matrix.md](openspec/changes/explore-production-refund-multi-agent/slide-implementation-matrix.md)  
任务清单：[tasks.md](openspec/changes/explore-production-refund-multi-agent/tasks.md)（按图分节）

## 状态

- **apply**：P0/P1 主线完成 — `pytest` **48 passed**（1 skipped: kubectl）。
- 命令：`ma-walkthrough`、`ma-api`、`scripts/ci.ps1`。
- P2：**LangGraph PoC** 见 [docs/langgraph-poc.md](docs/langgraph-poc.md)（`pip install -e ".[dev,langgraph]"`）。

```bash
pytest -m langgraph_poc
ma-langgraph-poc
```