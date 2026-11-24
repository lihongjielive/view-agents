"""HTTP API 客户端（默认 multi-agent health）。"""
from __future__ import annotations

import httpx

from agent_kit.config import Settings


def api_get(path: str = "/health", base_url: str | None = None) -> dict:
    settings = Settings.load()
    base = (base_url or settings.multi_agent_api_url).rstrip("/")
    url = path if path.startswith("http") else f"{base}{path}"
    try:
        r = httpx.get(url, timeout=5.0)
        return {"url": url, "status_code": r.status_code, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text}
    except httpx.HTTPError as exc:
        return {"url": url, "error": str(exc)}