from agent_memory.persona import PersonaStore


def test_persona_upsert_and_revoke(tmp_path):
    db = tmp_path / "p.db"
    p = PersonaStore(db)
    uid = "u1"
    p.ingest_user_message(uid, "以后写报告要附来源")
    facts = p.facts_for_task(uid, "写报告")
    assert facts
    p.ingest_user_message(uid, "写报告不需要来源了")
    facts2 = p.facts_for_task(uid, "写报告")
    assert not any("附来源" in f.content for f in facts2)