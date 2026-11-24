"""Resource 正文加载（文件系统，供 MCP resources/read）。"""
from __future__ import annotations

from pathlib import Path

_DOCS = Path(__file__).resolve().parents[2] / "docs" / "resources"

URIS = {
    "view-agents://protocol/execution-summary": _DOCS / "execution-summary.md",
    "view-agents://multi-agent/gateway-codes": _DOCS / "gateway-codes.md",
}


def read_uri(uri: str) -> str:
    path = URIS.get(uri)
    if not path or not path.is_file():
        raise FileNotFoundError(uri)
    return path.read_text(encoding="utf-8")