"""轻量内存向量库（教学用，无第三方 embedding）。"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass


def _tokenize(text: str) -> dict[str, float]:
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    if not tokens:
        return {}
    w = 1.0 / len(tokens)
    return {t: w for t in tokens}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values())) or 1.0
    nb = math.sqrt(sum(v * v for v in b.values())) or 1.0
    return dot / (na * nb)


@dataclass
class VectorRecord:
    doc_id: str
    text: str
    vector: dict[str, float]


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._records: list[VectorRecord] = []

    def add(self, text: str, doc_id: str | None = None) -> str:
        doc_id = doc_id or hashlib.sha256(text.encode()).hexdigest()[:12]
        self._records.append(VectorRecord(doc_id, text, _tokenize(text)))
        return doc_id

    def search(self, query: str, k: int = 3) -> list[tuple[float, VectorRecord]]:
        qv = _tokenize(query)
        scored = [(_cosine(qv, r.vector), r) for r in self._records]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]