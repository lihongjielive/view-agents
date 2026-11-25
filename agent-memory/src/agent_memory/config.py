"""配置与数据目录。"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    root: Path
    data_dir: Path
    openai_api_key: str | None
    embedding_model: str
    raw: dict

    @classmethod
    def load(cls) -> Settings:
        load_dotenv(_ROOT / ".env")
        raw = json.loads((_ROOT / "settings.json").read_text(encoding="utf-8"))
        data = _ROOT / os.getenv("AGENT_MEMORY_DATA_DIR", "data")
        data.mkdir(parents=True, exist_ok=True)
        return cls(
            root=_ROOT,
            data_dir=data,
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            embedding_model=os.getenv(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
            raw=raw,
        )

    def db_path(self, name: str) -> Path:
        return self.data_dir / name