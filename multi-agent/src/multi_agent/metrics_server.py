"""GET /metrics + /health（图 10）。"""
from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, Response

from multi_agent.metrics import MetricsCollector
from multi_agent.store import Store

app = FastAPI(title="multi-agent-metrics", version="0.1.0")

_store_path = ":memory:"
_override_collector: MetricsCollector | None = None


def configure_store_path(path: str) -> None:
    global _store_path, _override_collector
    _store_path = path
    _override_collector = None
    get_collector.cache_clear()


def set_collector(collector: MetricsCollector) -> None:
    """测试注入。"""
    global _override_collector
    _override_collector = collector
    get_collector.cache_clear()


@lru_cache
def get_collector() -> MetricsCollector:
    if _override_collector is not None:
        return _override_collector
    return MetricsCollector(Store(_store_path))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    body = get_collector().format_prometheus()
    return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")


def main() -> None:
    import os
    import uvicorn

    configure_store_path(os.getenv("MULTI_AGENT_STORE_PATH", ":memory:"))
    host = os.getenv("METRICS_HOST", "0.0.0.0")
    port = int(os.getenv("METRICS_PORT", "18081"))
    uvicorn.run("multi_agent.metrics_server:app", host=host, port=port, reload=False)