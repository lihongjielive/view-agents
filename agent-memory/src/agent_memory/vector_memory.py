"""④ 向量检索：分片存储 + 项目/时间筛选 + 相似度。"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from agent_memory.config import Settings
from agent_memory.embeddings import embed_text, similarity


@dataclass
class MemoryChunk:
    chunk_id: int
    project: str
    text: str
    created_at: str
    meta: dict


class VectorMemory:
    def __init__(self, db_path: Path | None = None) -> None:
        settings = Settings.load()
        self._path = db_path or settings.db_path("vectors.db")
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project TEXT NOT NULL,
                    text TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    meta_json TEXT
                )
                """
            )

    def add_chunk(
        self, text: str, project: str | None = None, meta: dict | None = None
    ) -> int:
        settings = Settings.load()
        project = project or settings.raw.get("vector", {}).get(
            "default_project", "default"
        )
        payload = embed_text(text)
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute(
                """
                INSERT INTO chunks (project, text, vector_json, created_at, meta_json)
                VALUES (?,?,?,?,?)
                """,
                (project, text, json.dumps(payload), now, json.dumps(meta or {})),
            )
            return int(cur.lastrowid)

    def retrieve(
        self,
        query: str,
        *,
        project: str | None = None,
        top_k: int | None = None,
        min_score: float = 0.05,
    ) -> list[tuple[float, MemoryChunk]]:
        settings = Settings.load()
        top_k = top_k or int(settings.raw.get("vector", {}).get("top_k", 3))
        qv = embed_text(query)
        sql = "SELECT id, project, text, vector_json, created_at, meta_json FROM chunks"
        params: list = []
        if project:
            sql += " WHERE project=?"
            params.append(project)
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(sql, params).fetchall()
        scored: list[tuple[float, MemoryChunk]] = []
        for r in rows:
            stored = json.loads(r[3])
            if isinstance(stored, dict) and "mode" not in stored:
                stored = {"mode": "bag", "v": stored}
            score = similarity(stored, qv)
            if score < min_score:
                continue
            chunk = MemoryChunk(r[0], r[1], r[2], r[4], json.loads(r[5] or "{}"))
            scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]