"""文本向量：词袋（默认）或 OpenAI embedding。"""
from __future__ import annotations

import math
import os
import re
from typing import Any

from agent_memory.config import Settings


def embed_mode() -> str:
    settings = Settings.load()
    default = settings.raw.get("vector", {}).get("embed_mode", "bag")
    return os.getenv("AGENT_MEMORY_EMBED_MODE", default)


def bag_embed(text: str) -> dict[str, float]:
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    if not tokens:
        return {}
    w = 1.0 / len(tokens)
    return {t: w for t in tokens}


def openai_embed(text: str) -> list[float] | None:
    settings = Settings.load()
    if not settings.openai_api_key:
        return None
    try:
        from langchain_openai import OpenAIEmbeddings

        emb = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )
        vec = emb.embed_query(text)
        return [float(x) for x in vec]
    except Exception:
        return None


def embed_text(text: str) -> dict[str, Any]:
    mode = embed_mode()
    if mode == "openai":
        vec = openai_embed(text)
        if vec is not None:
            return {"mode": "openai", "v": vec}
    return {"mode": "bag", "v": bag_embed(text)}


def similarity(stored: dict[str, Any], query: dict[str, Any]) -> float:
    if stored.get("mode") != query.get("mode"):
        qb = query if query.get("mode") == "bag" else stored
        sb = stored if query.get("mode") == "bag" else query
        if isinstance(sb.get("v"), dict) and isinstance(qb.get("v"), dict):
            return _cosine_bag(sb["v"], qb["v"])
        return 0.0
    v1, v2 = stored.get("v"), query.get("v")
    if isinstance(v1, dict) and isinstance(v2, dict):
        return _cosine_bag(v1, v2)
    if isinstance(v1, list) and isinstance(v2, list):
        return _cosine_list(v1, v2)
    return 0.0


def _cosine_bag(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values())) or 1.0
    nb = math.sqrt(sum(v * v for v in b.values())) or 1.0
    return dot / (na * nb)


def _cosine_list(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if not n:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(x * x for x in a[:n])) or 1.0
    nb = math.sqrt(sum(x * x for x in b[:n])) or 1.0
    return dot / (na * nb)