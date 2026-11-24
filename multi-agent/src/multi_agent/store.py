"""系统真相源：SQLite 持久化（图 02/04/06/07/08）。

表职责：
- workflows / tasks：租约（lease）、行版本（row_version）栅栏、DAG 依赖
- tool_operations：business_key 幂等镜像
- outbox_events + consumed_events：至少一次投递 + 消费幂等（图 06）
- audit_log：Gateway / 支付 POST 留痕
- reconciliation_queue：NEEDS_REVIEW 入队（图 08）

P2：`postgres_store.PostgresStore` 复用本类全部方法，仅换连接层。
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Generator, Iterable

from multi_agent.domain import TaskStatus, ToolOpStatus, WorkflowStatus, make_business_key
from multi_agent.state_machine import assert_task_transition, assert_tool_op_transition

UTC = timezone.utc


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s)


@dataclass
class TaskRow:
    """任务行只读视图；Worker 用 row_version/attempt_no 做 fenced 更新（图 07）。"""

    id: str
    workflow_id: str
    logical_step_key: str
    status: TaskStatus
    owner: str | None
    attempt_no: int
    row_version: int
    lease_until: datetime | None
    depends_on_task_id: str | None
    result_version: int
    business_key: str | None


class Store:
    """唯一业务真相；LangGraph / HTTP 提议层不得绕过本层写支付。"""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    @contextmanager
    def tx(self) -> Generator[sqlite3.Connection, None, None]:
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                tenant TEXT NOT NULL,
                order_id TEXT NOT NULL,
                after_sale_id TEXT NOT NULL,
                approval_snapshot_id TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                logical_step_key TEXT NOT NULL,
                status TEXT NOT NULL,
                owner TEXT,
                attempt_no INTEGER NOT NULL DEFAULT 0,
                row_version INTEGER NOT NULL DEFAULT 1,
                lease_until TEXT,
                depends_on_task_id TEXT,
                result_version INTEGER NOT NULL DEFAULT 0,
                business_key TEXT UNIQUE,
                created_at TEXT NOT NULL,
                UNIQUE(workflow_id, logical_step_key)
            );
            CREATE TABLE IF NOT EXISTS tool_operations (
                business_key TEXT PRIMARY KEY,
                tool_name TEXT NOT NULL,
                status TEXT NOT NULL,
                task_id TEXT NOT NULL,
                remote_ref TEXT,
                payload_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS outbox_events (
                id TEXT PRIMARY KEY,
                aggregate_type TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                published_at TEXT,
                idempotency_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                detail_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS consumed_events (
                idempotency_key TEXT PRIMARY KEY,
                consumed_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reconciliation_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                business_key TEXT NOT NULL,
                status TEXT NOT NULL,
                detail_json TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    # --- 图 08：人工/对账队列 ---

    def escalate_needs_review(
        self, workflow_id: str, *, task_id: str, reason: str, business_key: str
    ) -> None:
        """图 08：远端不可查 → 工作流 NEEDS_REVIEW，禁止盲重试 POST。"""
        self.set_workflow_status(workflow_id, WorkflowStatus.NEEDS_REVIEW)
        with self.tx():
            self._conn.execute(
                """
                INSERT INTO reconciliation_queue (workflow_id, business_key, status,
                    detail_json, created_at)
                VALUES (?, ?, 'OPEN', ?, ?)
                """,
                (workflow_id, business_key, json.dumps({"reason": reason, "task_id": task_id}), _iso(_utcnow())),
            )
        self.audit("system", "needs_review", {"workflow_id": workflow_id, "reason": reason})

    def reconciliation_open_count(self, workflow_id: str | None = None) -> int:
        if workflow_id:
            row = self._conn.execute(
                "SELECT COUNT(*) c FROM reconciliation_queue WHERE workflow_id=? AND status='OPEN'",
                (workflow_id,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) c FROM reconciliation_queue WHERE status='OPEN'"
            ).fetchone()
        return int(row["c"])

    # --- 图 01/04：建单 + refund/coupon 双子任务 + business_key ---

    def create_workflow(
        self,
        *,
        tenant: str,
        order_id: str,
        after_sale_id: str,
        refund_amount: float,
        approval_snapshot_id: str = "appr-default",
    ) -> str:
        wf_id = str(uuid.uuid4())
        now = _iso(_utcnow())
        bk_refund = make_business_key(
            tenant, "refund.create", order_id, after_sale_id
        )
        bk_coupon = make_business_key(
            tenant, "coupon.issue", order_id, after_sale_id
        )
        refund_id = str(uuid.uuid4())
        coupon_id = str(uuid.uuid4())
        with self.tx():
            self._conn.execute(
                """
                INSERT INTO workflows (id, status, version, tenant, order_id,
                    after_sale_id, approval_snapshot_id, created_at)
                VALUES (?, ?, 1, ?, ?, ?, ?, ?)
                """,
                (
                    wf_id,
                    WorkflowStatus.RUNNING.value,
                    tenant,
                    order_id,
                    after_sale_id,
                    approval_snapshot_id,
                    now,
                ),
            )
            self._conn.execute(
                """
                INSERT INTO tasks (id, workflow_id, logical_step_key, status,
                    attempt_no, row_version, business_key, created_at)
                VALUES (?, ?, 'refund', ?, 0, 1, ?, ?)
                """,
                (refund_id, wf_id, TaskStatus.READY.value, bk_refund, now),
            )
            self._conn.execute(
                """
                INSERT INTO tasks (id, workflow_id, logical_step_key, status,
                    depends_on_task_id, attempt_no, row_version, business_key, created_at)
                VALUES (?, ?, 'coupon', ?, ?, 0, 1, ?, ?)
                """,
                (
                    coupon_id,
                    wf_id,
                    TaskStatus.WAITING.value,
                    refund_id,
                    bk_coupon,
                    now,
                ),
            )
            self._insert_outbox_in_tx(
                "workflow",
                wf_id,
                "workflow.created",
                {"workflow_id": wf_id, "refund_amount": refund_amount},
                f"workflow.created:{wf_id}",
            )
        return wf_id

    def get_task(self, task_id: str) -> TaskRow | None:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        return self._task_from_row(row) if row else None

    def list_tasks(self, workflow_id: str) -> list[TaskRow]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE workflow_id=? ORDER BY created_at",
            (workflow_id,),
        ).fetchall()
        return [self._task_from_row(r) for r in rows]

    def get_workflow_status(self, workflow_id: str) -> WorkflowStatus:
        row = self._conn.execute(
            "SELECT status FROM workflows WHERE id=?", (workflow_id,)
        ).fetchone()
        if not row:
            raise KeyError(workflow_id)
        return WorkflowStatus(row["status"])

    def set_workflow_status(self, workflow_id: str, status: WorkflowStatus) -> None:
        from multi_agent.state_machine import assert_workflow_transition

        current = self.get_workflow_status(workflow_id)
        assert_workflow_transition(current, status)
        self._conn.execute(
            "UPDATE workflows SET status=?, version=version+1 WHERE id=?",
            (status.value, workflow_id),
        )
        self._conn.commit()

    def count_unpublished_outbox(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS c FROM outbox_events WHERE published_at IS NULL"
        ).fetchone()
        return int(row["c"])

    # --- 图 07：租约认领（attempt_no 在过期重领时递增）---

    def claim_task(
        self, task_id: str, owner: str, lease_seconds: int = 30
    ) -> TaskRow | None:
        """Lease + attempt increment (new claim after expiry)."""
        with self.tx():
            row = self._conn.execute(
                "SELECT * FROM tasks WHERE id=?", (task_id,)
            ).fetchone()
            if not row:
                return None
            status = TaskStatus(row["status"])
            if status not in (TaskStatus.READY, TaskStatus.UNKNOWN):
                return None
            lease_until = _parse_iso(row["lease_until"])
            now = _utcnow()
            if lease_until and lease_until > now and row["owner"] and row["owner"] != owner:
                return None
            if lease_until and lease_until > now and row["owner"] == owner:
                new_attempt = row["attempt_no"]
            else:
                new_attempt = row["attempt_no"] + 1
            new_lease = now + timedelta(seconds=lease_seconds)
            assert_task_transition(status, TaskStatus.CLAIMED)
            cur = self._conn.execute(
                """
                UPDATE tasks SET status=?, owner=?, attempt_no=?, lease_until=?,
                    row_version=row_version+1
                WHERE id=? AND row_version=? AND status IN ('READY', 'UNKNOWN')
                """,
                (
                    TaskStatus.CLAIMED.value,
                    owner,
                    new_attempt,
                    _iso(new_lease),
                    task_id,
                    row["row_version"],
                ),
            )
            if cur.rowcount == 0:
                return None
        return self.get_task(task_id)

    # --- 图 07：条件更新；旧 Worker 因 row_version/lease 不匹配得 rowcount=0 ---

    def fenced_task_update(
        self,
        *,
        task_id: str,
        owner: str,
        attempt_no: int,
        row_version: int,
        to_status: TaskStatus,
        bump_result: bool = False,
    ) -> bool:
        """Slide 07: conditional update; old worker gets 0 rows."""
        task = self.get_task(task_id)
        if not task:
            return False
        now = _utcnow()
        lease_ok = task.lease_until and task.lease_until > now
        rv = task.row_version
        result_version = task.result_version + (1 if bump_result else 0)
        cur = self._conn.execute(
            """
            UPDATE tasks SET status=?, row_version=row_version+1,
                result_version=?, owner=NULL, lease_until=NULL
            WHERE id=? AND owner=? AND attempt_no=? AND row_version=?
              AND lease_until > ?
            """,
            (
                to_status.value,
                result_version,
                task_id,
                owner,
                attempt_no,
                row_version,
                _iso(now),
            ),
        )
        return cur.rowcount == 1

    def set_task_running(self, task_id: str, owner: str, attempt_no: int) -> None:
        task = self.get_task(task_id)
        if not task:
            raise KeyError(task_id)
        assert_task_transition(task.status, TaskStatus.RUNNING)
        self._conn.execute(
            """
            UPDATE tasks SET status=? WHERE id=? AND owner=? AND attempt_no=?
            """,
            (TaskStatus.RUNNING.value, task_id, owner, attempt_no),
        )
        self._conn.commit()

    def upsert_tool_operation_pending(
        self, *, business_key: str, tool_name: str, task_id: str, payload: dict
    ) -> None:
        now = _iso(_utcnow())
        with self.tx():
            existing = self._conn.execute(
                "SELECT status FROM tool_operations WHERE business_key=?",
                (business_key,),
            ).fetchone()
            if existing:
                return
            self._conn.execute(
                """
                INSERT INTO tool_operations (business_key, tool_name, status, task_id,
                    payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    business_key,
                    tool_name,
                    ToolOpStatus.PENDING.value,
                    task_id,
                    json.dumps(payload),
                    now,
                    now,
                ),
            )

    def update_tool_operation(
        self,
        business_key: str,
        to_status: ToolOpStatus,
        *,
        remote_ref: str | None = None,
        extra: dict | None = None,
    ) -> None:
        row = self._conn.execute(
            "SELECT status, payload_json FROM tool_operations WHERE business_key=?",
            (business_key,),
        ).fetchone()
        if not row:
            raise KeyError(business_key)
        assert_tool_op_transition(ToolOpStatus(row["status"]), to_status)
        payload = json.loads(row["payload_json"] or "{}")
        if extra:
            payload.update(extra)
        self._conn.execute(
            """
            UPDATE tool_operations SET status=?, remote_ref=?, payload_json=?, updated_at=?
            WHERE business_key=?
            """,
            (
                to_status.value,
                remote_ref,
                json.dumps(payload),
                _iso(_utcnow()),
                business_key,
            ),
        )
        self._conn.commit()

    def get_tool_operation(self, business_key: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM tool_operations WHERE business_key=?", (business_key,)
        ).fetchone()
        if not row:
            return None
        return dict(row)

    # --- 图 09：DAG — 退款 result_version 有效后才 READY 发券 ---

    def try_promote_coupon_after_refund(self, workflow_id: str) -> bool:
        """退款 SUCCEEDED 且 result_version≥1 时，coupon 由 WAITING→READY 并写 outbox。"""
        tasks = {t.logical_step_key: t for t in self.list_tasks(workflow_id)}
        refund = tasks.get("refund")
        coupon = tasks.get("coupon")
        if not refund or not coupon:
            return False
        if refund.status != TaskStatus.SUCCEEDED or refund.result_version < 1:
            return False
        if coupon.status != TaskStatus.WAITING:
            return False
        promoted = False
        with self.tx():
            cur = self._conn.execute(
                """
                UPDATE tasks SET status=?, row_version=row_version+1
                WHERE id=? AND status='WAITING'
                """,
                (TaskStatus.READY.value, coupon.id),
            )
            if cur.rowcount:
                promoted = True
                self._insert_outbox_in_tx(
                    "task",
                    coupon.id,
                    "task.ready",
                    {"task_id": coupon.id, "step": "coupon"},
                    f"task.ready:{coupon.id}:v{refund.result_version}",
                )
        return promoted

    # --- 图 06：事务内写 outbox，与业务同事务提交 ---

    def _insert_outbox_in_tx(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict,
        idempotency_key: str,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO outbox_events (id, aggregate_type, aggregate_id, event_type,
                payload_json, idempotency_key, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                aggregate_type,
                aggregate_id,
                event_type,
                json.dumps(payload),
                idempotency_key,
                _iso(_utcnow()),
            ),
        )

    def fetch_unpublished_outbox(self, limit: int = 50) -> list[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT * FROM outbox_events WHERE published_at IS NULL
            ORDER BY created_at LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def mark_outbox_published(self, event_id: str, *, simulate_loss: bool = False) -> None:
        if simulate_loss:
            return
        self._conn.execute(
            "UPDATE outbox_events SET published_at=? WHERE id=?",
            (_iso(_utcnow()), event_id),
        )
        self._conn.commit()

    def consume_event_idempotent(self, idempotency_key: str) -> bool:
        """Return True if first consume (slide 06)."""
        with self.tx():
            hit = self._conn.execute(
                "SELECT 1 FROM consumed_events WHERE idempotency_key=?",
                (idempotency_key,),
            ).fetchone()
            if hit:
                return False
            self._conn.execute(
                "INSERT INTO consumed_events (idempotency_key, consumed_at) VALUES (?, ?)",
                (idempotency_key, _iso(_utcnow())),
            )
            return True

    def audit(self, actor: str, action: str, detail: dict) -> None:
        self._conn.execute(
            "INSERT INTO audit_log (ts, actor, action, detail_json) VALUES (?, ?, ?, ?)",
            (_iso(_utcnow()), actor, action, json.dumps(detail)),
        )
        self._conn.commit()

    def count_audit(self, action: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS c FROM audit_log WHERE action=?", (action,)
        ).fetchone()
        return int(row["c"])

    def count_http_posts_to_payment(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS c FROM audit_log WHERE action='payment.post_refund'"
        ).fetchone()
        return int(row["c"])

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> TaskRow:
        return TaskRow(
            id=row["id"],
            workflow_id=row["workflow_id"],
            logical_step_key=row["logical_step_key"],
            status=TaskStatus(row["status"]),
            owner=row["owner"],
            attempt_no=row["attempt_no"],
            row_version=row["row_version"],
            lease_until=_parse_iso(row["lease_until"]),
            depends_on_task_id=row["depends_on_task_id"],
            result_version=row["result_version"],
            business_key=row["business_key"],
        )

    def close(self) -> None:
        self._conn.close()