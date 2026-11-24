"""Multi-Agent：可恢复执行业务协议（Python 仿真，对照 docx 图 01–11）。

关键点速览：
- **真相源**：`Store`（SQLite / 可选 `PostgresStore`），非 LLM messages
- **提议 vs 执行**：`proposals.submit_proposal` → `ToolGateway.evaluate`（图 03）
- **编排**：`SupervisorEngine` 调度 `RefundWorker` / `CouponWorker`（图 01）
- **幂等写入键**：`domain.make_business_key`（图 04）
- **状态机**：`state_machine.*_TRANSITIONS`（图 05 UNKNOWN）
- **事件**：`OutboxPipeline` 发布/消费（图 06）
- **租约栅栏**：`Store.claim_task` + `fenced_task_update`（图 07）
- **对账**：`RefundWorker.reconcile`、NEEDS_REVIEW（图 08）
- **DAG**：退款成功 → `try_promote_coupon_after_refund`（图 09）
- **观测**：`metrics.MetricsCollector`（图 10）
- **可选 LLM 层**：`langgraph_poc`（图 03 提议语义，P2）
"""

__version__ = "0.1.0"