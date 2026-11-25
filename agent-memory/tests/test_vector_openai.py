import json
from unittest.mock import MagicMock, patch

from agent_memory.embeddings import embed_text, similarity
from agent_memory.vector_memory import VectorMemory


def test_embed_openai_mock(monkeypatch):
    monkeypatch.setenv("AGENT_MEMORY_EMBED_MODE", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    with patch("langchain_openai.OpenAIEmbeddings") as cls:
        cls.return_value.embed_query.return_value = [1.0, 0.0, 0.0]
        payload = embed_text("hello")
        assert payload["mode"] == "openai"
        assert len(payload["v"]) == 3


def test_openai_similarity_lists():
    a = {"mode": "openai", "v": [1.0, 0.0]}
    b = {"mode": "openai", "v": [1.0, 0.0]}
    assert similarity(a, b) > 0.99


def test_vector_legacy_bag_rows(tmp_path):
    """P0 行仅存 bag dict 时仍可检索。"""
    db = tmp_path / "v.db"
    v = VectorMemory(db)
    import sqlite3

    from agent_memory.embeddings import bag_embed

    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO chunks (project,text,vector_json,created_at,meta_json) VALUES (?,?,?,?,?)",
            ("p", "方案 A", json.dumps(bag_embed("方案 A")), "t", "{}"),
        )
    hits = v.retrieve("方案 A", project="p", min_score=0.01)
    assert hits