"""运维指标（图 10）：从 Store 聚合 backlog / UNKNOWN / outbox lag。

HPA 样板见 deploy/k8s/；metric 名与 Prometheus 约定见 docs/observability.md。
"""
from __future__ import annotations

from datetime import datetime, timezone

from multi_agent.domain import TaskStatus, ToolOpStatus, WorkflowStatus
from multi_agent.store import Store, _parse_iso, _utcnow

UTC = timezone.utc

# 交接侧：未发布 outbox 条数 ≈ 合成 kafka lag
METRIC_KAFKA_CONSUMER_LAG = "multi_agent_kafka_consumer_lag"
METRIC_READY_PENDING = "multi_agent_task_ready_pending_count"
METRIC_READY_OLDEST_AGE = "multi_agent_task_ready_oldest_age_seconds"
METRIC_UNKNOWN_OPS = "multi_agent_unknown_operations_count"
METRIC_OUTBOX_UNPUBLISHED = "multi_agent_outbox_unpublished_count"
METRIC_COMPENSATION_BACKLOG = "multi_agent_compensation_workflow_count"
METRIC_LEASE_RENEW_FAILURES = "multi_agent_lease_renew_failure_total"


class MetricsCollector:
    """从 Store 聚合图 10 所列指标。"""

    def __init__(self, store: Store) -> None:
        self.store = store
        self._lease_renew_failures = 0

    def record_lease_renew_failure(self) -> None:
        self._lease_renew_failures += 1

    def collect(self) -> dict[str, float]:
        now = _utcnow()
        unknown_ops = self._scalar(
            "SELECT COUNT(*) c FROM tool_operations WHERE status=?",
            (ToolOpStatus.UNKNOWN.value,),
        )
        ready_pending = self._scalar(
            "SELECT COUNT(*) c FROM tasks WHERE status=?",
            (TaskStatus.READY.value,),
        )
        oldest = self.store._conn.execute(
            "SELECT MIN(created_at) AS m FROM tasks WHERE status=?",
            (TaskStatus.READY.value,),
        ).fetchone()["m"]
        oldest_age = 0.0
        if oldest:
            dt = _parse_iso(oldest)
            if dt:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                oldest_age = max(0.0, (now - dt).total_seconds())

        unpublished = float(self.store.count_unpublished_outbox())
        compensating = self._scalar(
            "SELECT COUNT(*) c FROM workflows WHERE status=?",
            (WorkflowStatus.COMPENSATING.value,),
        )
        return {
            METRIC_UNKNOWN_OPS: unknown_ops,
            METRIC_READY_PENDING: ready_pending,
            METRIC_READY_OLDEST_AGE: oldest_age,
            METRIC_KAFKA_CONSUMER_LAG: unpublished,
            METRIC_OUTBOX_UNPUBLISHED: unpublished,
            METRIC_COMPENSATION_BACKLOG: compensating,
            METRIC_LEASE_RENEW_FAILURES: float(self._lease_renew_failures),
        }

    def format_prometheus(self) -> str:
        lines = []
        for name, value in self.collect().items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        return "\n".join(lines) + "\n"

    def _scalar(self, sql: str, params: tuple = ()) -> float:
        row = self.store._conn.execute(sql, params).fetchone()
        return float(row["c"])


def snapshot_metrics(store: Store) -> dict[str, float]:
    """向后兼容。"""
    return MetricsCollector(store).collect()