"""Outbox 发布/消费管道（图 06；进程内模拟 Kafka）。

- publish_pending：标记 published_at（可注入 simulate_ack_loss）
- ingest_all：按 idempotency_key 幂等消费，驱动下游逻辑占位
"""
from __future__ import annotations

import json
from multi_agent.store import Store


class OutboxPipeline:
    """与 Store 同事务写入的 outbox 行，在这里异步「交接」给 Worker/消费端。"""

    def __init__(self, store: Store) -> None:
        self.store = store

    def publish_pending(self, *, simulate_ack_loss: bool = False) -> int:
        rows = self.store.fetch_unpublished_outbox()
        n = 0
        for row in rows:
            self.store.mark_outbox_published(row["id"], simulate_loss=simulate_ack_loss)
            n += 1
        return n

    def ingest_all(self) -> int:
        """Idempotent consume of published events (replay-safe)."""
        rows = self.store._conn.execute(
            """
            SELECT * FROM outbox_events WHERE published_at IS NOT NULL
            ORDER BY created_at
            """
        ).fetchall()
        ingested = 0
        for row in rows:
            key = row["idempotency_key"]
            if not self.store.consume_event_idempotent(key):
                continue
            payload = json.loads(row["payload_json"])
            if row["event_type"] == "task.ready":
                ingested += 1
            elif row["event_type"] == "workflow.created":
                ingested += 1
        return ingested