from agent_memory.coordinator import MemoryCoordinator
from agent_memory.persona import PersonaStore
from agent_memory.session import SessionStore, StepStatus
from agent_memory.vector_memory import VectorMemory


def test_coordinator_assembles_all(tmp_path):
    coord = MemoryCoordinator(
        session=SessionStore(tmp_path / "s.db"),
        persona=PersonaStore(tmp_path / "p.db"),
        vectors=VectorMemory(tmp_path / "v.db"),
    )
    sid = coord.session.create_session()
    coord.persona.ingest_user_message("u1", "以后写报告要附来源")
    coord.vectors.add_chunk("选定方案 A", project="demo")
    coord.session.append_message(sid, "user", "继续写报告")
    coord.session.set_checkpoint(sid, "citations", StepStatus.IN_PROGRESS, "进行中")
    ctx = coord.build_context(sid, "u1", task_hint="写报告")
    assert "用户画像" in ctx.full_text
    assert "检查点" in ctx.full_text