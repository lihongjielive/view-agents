from agent_memory.compression import compress_messages, maybe_compress
from agent_memory.session import Message


def test_compress_extracts_constraints():
    msgs = [
        Message(1, "s", "user", "写报告必须附来源", {}, "t"),
        Message(2, "s", "assistant", "好的", {}, "t"),
    ]
    s = compress_messages(msgs)
    assert s.goal
    assert s.constraints or "来源" in s.to_text()


def test_maybe_compress_splits():
    msgs = [
        Message(i, "s", "user" if i % 2 else "assistant", f"msg{i}", {}, "t")
        for i in range(1, 16)
    ]
    summary, recent = maybe_compress(msgs, recent_n=4, threshold=10)
    assert summary is not None
    assert len(recent) == 4