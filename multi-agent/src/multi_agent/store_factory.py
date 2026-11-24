"""Store 工厂：环境变量 MULTI_AGENT_STORE_URL 切换 SQLite / Postgres（P2）。"""
from __future__ import annotations

import os
from pathlib import Path

from multi_agent.postgres_store import PostgresStore
from multi_agent.store import Store


def open_store(url: str | None = None) -> Store:
    """``sqlite::memory:`` / ``sqlite:./data/ma.db`` / ``postgresql://...``。"""
    url = url or os.environ.get("MULTI_AGENT_STORE_URL", "sqlite::memory:")
    lowered = url.lower()
    if lowered.startswith(("postgres://", "postgresql://")):
        return PostgresStore(url)
    if lowered.startswith("sqlite:"):
        path = url.split(":", 1)[1]
        if path in ("", ":memory:"):
            path = ":memory:"
        return Store(path)
    return Store(Path(url))