from agent_memory.vector_memory import VectorMemory


def test_vector_retrieve_project(tmp_path):
    db = tmp_path / "v.db"
    v = VectorMemory(db)
    v.add_chunk("方案 A 与 B 比较后选定 A", project="p1")
    v.add_chunk("无关的烹饪食谱", project="p2")
    hits = v.retrieve("方案 A 比较", project="p1", min_score=0.01)
    assert hits
    assert "方案" in hits[0][1].text