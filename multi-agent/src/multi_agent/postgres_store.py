"""P2：PostgreSQL 适配 —— 复用 Store 全部 SQL，_PgConnAdapter 做占位符转换。

DDL 见 deploy/postgres/schema.sql；URL 经 store_factory.open_store 解析。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from multi_agent.store import Store

_SCHEMA = (
    Path(__file__).resolve().parents[2] / "deploy" / "postgres" / "schema.sql"
)


class _PgConnAdapter:
    """Wrap psycopg connection so Store SQL can keep SQLite-style placeholders."""

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def execute(self, sql: str, params: tuple | list = ()) -> Any:
        return self._conn.execute(sql.replace("?", "%s"), params)

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()


class PostgresStore(Store):
    """与 `Store` 相同 API；`dsn` 形如 `postgresql://user:pass@host/db`。"""

    def __init__(self, dsn: str) -> None:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as e:
            raise ImportError(
                "PostgresStore requires psycopg: pip install -e '.[postgres]'"
            ) from e

        self.path = dsn
        raw = psycopg.connect(dsn, row_factory=dict_row, autocommit=False)
        self._conn = _PgConnAdapter(raw)
        self._init_schema_postgres()

    def _init_schema_postgres(self) -> None:
        ddl = _SCHEMA.read_text(encoding="utf-8")
        with self.tx():
            for stmt in ddl.split(";"):
                chunk = stmt.strip()
                if chunk:
                    self._conn.execute(chunk)
        self._conn.commit()