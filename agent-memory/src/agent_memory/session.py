"""① 会话与任务状态：消息 + 检查点 + 制品。"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from agent_memory.config import Settings


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class Message:
    id: int
    session_id: str
    role: str
    content: str
    meta: dict[str, Any]
    created_at: str


@dataclass
class TaskCheckpoint:
    session_id: str
    step: str
    status: StepStatus
    description: str
    artifact: dict[str, Any] | None = None


class SessionStore:
    def __init__(self, db_path: Path | None = None) -> None:
        settings = Settings.load()
        self._path = db_path or settings.db_path("sessions.db")
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    topic TEXT
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    meta_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS checkpoints (
                    session_id TEXT NOT NULL,
                    step TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT,
                    artifact_json TEXT,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, step)
                );
                """
            )

    def create_session(self, topic: str = "") -> str:
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, created_at, topic) VALUES (?,?,?)",
                (sid, now, topic),
            )
        return sid

    def append_message(
        self, session_id: str, role: str, content: str, meta: dict | None = None
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute(
                """
                INSERT INTO messages (session_id, role, content, meta_json, created_at)
                VALUES (?,?,?,?,?)
                """,
                (session_id, role, content, json.dumps(meta or {}), now),
            )
            return int(cur.lastrowid)

    def list_messages(self, session_id: str, limit: int | None = None) -> list[Message]:
        sql = """
            SELECT id, session_id, role, content, meta_json, created_at
            FROM messages WHERE session_id=? ORDER BY id
        """
        if limit:
            sql += f" LIMIT {int(limit)}"
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(sql, (session_id,)).fetchall()
        return [
            Message(
                id=r[0],
                session_id=r[1],
                role=r[2],
                content=r[3],
                meta=json.loads(r[4] or "{}"),
                created_at=r[5],
            )
            for r in rows
        ]

    def get_message(self, message_id: int) -> Message | None:
        with sqlite3.connect(self._path) as conn:
            row = conn.execute(
                """
                SELECT id, session_id, role, content, meta_json, created_at
                FROM messages WHERE id=?
                """,
                (message_id,),
            ).fetchone()
        if not row:
            return None
        return Message(
            row[0], row[1], row[2], row[3], json.loads(row[4] or "{}"), row[5]
        )

    def set_checkpoint(
        self,
        session_id: str,
        step: str,
        status: StepStatus,
        description: str = "",
        artifact: dict | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (session_id, step, status, description, artifact_json, updated_at)
                VALUES (?,?,?,?,?,?)
                ON CONFLICT(session_id, step) DO UPDATE SET
                    status=excluded.status,
                    description=excluded.description,
                    artifact_json=excluded.artifact_json,
                    updated_at=excluded.updated_at
                """,
                (
                    session_id,
                    step,
                    status.value,
                    description,
                    json.dumps(artifact or {}),
                    now,
                ),
            )

    def list_checkpoints(self, session_id: str) -> list[TaskCheckpoint]:
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(
                """
                SELECT session_id, step, status, description, artifact_json
                FROM checkpoints WHERE session_id=? ORDER BY step
                """,
                (session_id,),
            ).fetchall()
        out: list[TaskCheckpoint] = []
        for r in rows:
            out.append(
                TaskCheckpoint(
                    session_id=r[0],
                    step=r[1],
                    status=StepStatus(r[2]),
                    description=r[3] or "",
                    artifact=json.loads(r[4] or "{}") or None,
                )
            )
        return out

    def recent_turns(self, session_id: str, n: int) -> list[Message]:
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(
                """
                SELECT id, session_id, role, content, meta_json, created_at
                FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?
                """,
                (session_id, n),
            ).fetchall()
        rows.reverse()
        return [
            Message(r[0], r[1], r[2], r[3], json.loads(r[4] or "{}"), r[5]) for r in rows
        ]