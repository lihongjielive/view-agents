from agent_kit.memory_adapter import coordinator_enabled, try_load_coordinator


def test_coordinator_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AGENT_KIT_USE_COORDINATOR", raising=False)
    assert not coordinator_enabled()
    assert try_load_coordinator() is None


def test_coordinator_missing_package(monkeypatch):
    monkeypatch.setenv("AGENT_KIT_USE_COORDINATOR", "1")
    assert coordinator_enabled()
    # agent-memory 未安装时可回落 None；已安装 monorepo 时应非 None
    _ = try_load_coordinator()