from agent_kit.memory.base import SQLiteMemory
from agent_kit.memory.vector_store import InMemoryVectorStore


def test_sqlite_memory_roundtrip(tmp_path):
    mem = SQLiteMemory(db_path=tmp_path / "h.db")
    mem.add_turn("user", "hello")
    assert "hello" in mem.session_context()


def test_vector_search():
    vs = InMemoryVectorStore()
    vs.add("北京天气晴朗")
    vs.add("上海下雨")
    hits = vs.search("北京旅行")
    assert hits[0][1].text.startswith("北京")


def test_kit_agent_memory_search_examples():
    from agent_kit.agents.agent import KitAgent

    agent = KitAgent()
    hits = agent.memory_search("旅行规划", k=2)
    assert hits
    assert any("旅行" in h or "北京" in h for h in hits)