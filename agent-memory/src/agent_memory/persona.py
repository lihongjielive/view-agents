"""③ 事实与画像：跨会话用户偏好。"""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from agent_memory.config import Settings


@dataclass
class UserFact:
    user_id: str
    fact_key: str
    content: str
    source: str
    confidence: str
    updated_at: str


_CANDIDATE_PATTERNS = [
    re.compile(r"以后(.{2,40}?)(?:要|记得|必须)"),
    re.compile(r"写报告要(.{2,40})"),
    re.compile(r"请记住[：:](.+)"),
]


def extract_candidate_facts(user_text: str) -> list[tuple[str, str]]:
    """(fact_key, content) 候选。"""
    found: list[tuple[str, str]] = []
    for pat in _CANDIDATE_PATTERNS:
        for m in pat.finditer(user_text):
            content = m.group(0).strip()
            key = f"pref:{hash(content) & 0xFFFF:x}"
            found.append((key, content))
    if "附来源" in user_text:
        found.append(("writing.attach_sources", "写报告要附来源"))
    return found


class PersonaStore:
    def __init__(self, db_path: Path | None = None) -> None:
        settings = Settings.load()
        self._path = db_path or settings.db_path("persona.db")
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    user_id TEXT NOT NULL,
                    fact_key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    confidence TEXT DEFAULT 'high',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, fact_key)
                )
                """
            )

    def upsert_fact(
        self,
        user_id: str,
        fact_key: str,
        content: str,
        source: str = "user",
        confidence: str = "high",
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                INSERT INTO facts (user_id, fact_key, content, source, confidence, updated_at)
                VALUES (?,?,?,?,?,?)
                ON CONFLICT(user_id, fact_key) DO UPDATE SET
                    content=excluded.content,
                    source=excluded.source,
                    confidence=excluded.confidence,
                    updated_at=excluded.updated_at
                """,
                (user_id, fact_key, content, source, confidence, now),
            )

    def delete_fact(self, user_id: str, fact_key: str) -> bool:
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute(
                "DELETE FROM facts WHERE user_id=? AND fact_key=?",
                (user_id, fact_key),
            )
            return cur.rowcount > 0

    def ingest_user_message(self, user_id: str, text: str) -> list[str]:
        """从用户话里提取并写入画像；返回写入的 fact_key。"""
        keys: list[str] = []
        if "不需要来源" in text or "不用附来源" in text:
            self.delete_fact(user_id, "writing.attach_sources")
            with sqlite3.connect(self._path) as conn:
                conn.execute(
                    "DELETE FROM facts WHERE user_id=? AND content LIKE ?",
                    (user_id, "%附来源%"),
                )
            keys.append("writing.attach_sources:deleted")
            return keys
        for key, content in extract_candidate_facts(text):
            self.upsert_fact(user_id, key, content, source="explicit_user")
            keys.append(key)
        return keys

    def facts_for_task(self, user_id: str, task_hint: str = "") -> list[UserFact]:
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(
                """
                SELECT user_id, fact_key, content, source, confidence, updated_at
                FROM facts WHERE user_id=?
                """,
                (user_id,),
            ).fetchall()
        facts = [
            UserFact(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows
        ]
        if not task_hint:
            return facts
        hint = task_hint.lower()
        if "报告" in task_hint or "report" in hint:
            return [f for f in facts if "writing" in f.fact_key or "报告" in f.content]
        return facts