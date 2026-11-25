from agent_memory.session import SessionStore, StepStatus


def test_session_and_checkpoints(tmp_path):
    db = tmp_path / "s.db"
    store = SessionStore(db)
    sid = store.create_session("report")
    store.append_message(sid, "user", "写报告")
    store.set_checkpoint(sid, "step1", StepStatus.COMPLETED, "done")
    assert len(store.list_messages(sid)) == 1
    assert store.list_checkpoints(sid)[0].status == StepStatus.COMPLETED