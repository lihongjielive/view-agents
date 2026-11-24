"""短期会话 + SQLite 长期历史。"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from agent_kit.config import Settings


@dataclass
class Turn:
    role: str
    content: str
    meta: dict | None = None


class SQLiteMemory:
    def __init__(self, db_path: Path | None = None) -> None:
        settings = Settings.load()
        path = db_path or (settings.memory_dir / "history.db")
        self._path = path
        self._session: list[Turn] = []
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    meta_json TEXT
                )
                """
            )

    def add_turn(self, role: str, content: str, meta: dict | None = None) -> None:
        turn = Turn(role=role, content=content, meta=meta)
        self._session.append(turn)
        max_turns = int(Settings.load().raw.get("memory", {}).get("session_max_turns", 20))
        if len(self._session) > max_turns:
            self._session = self._session[-max_turns:]
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                "INSERT INTO turns (created_at, role, content, meta_json) VALUES (?,?,?,?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    role,
                    content,
                    json.dumps(meta or {}, ensure_ascii=False),
                ),
            )

    def session_context(self) -> str:
        return "\n".join(f"{t.role}: {t.content}" for t in self._session[-6:])