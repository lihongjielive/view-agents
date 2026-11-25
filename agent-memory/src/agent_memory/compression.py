"""② 摘要压缩：历史消息 → 目标/约束/决定/待办。"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from agent_memory.session import Message


@dataclass
class ConversationSummary:
    goal: str = ""
    constraints: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    progress: list[str] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)
    compressed_from_message_ids: list[int] = field(default_factory=list)

    def to_text(self) -> str:
        lines = ["【历史摘要】"]
        if self.goal:
            lines.append(f"目标: {self.goal}")
        if self.constraints:
            lines.append("约束: " + "; ".join(self.constraints))
        if self.decisions:
            lines.append("已决定: " + "; ".join(self.decisions))
        if self.progress:
            lines.append("已完成: " + "; ".join(self.progress))
        if self.todos:
            lines.append("待办: " + "; ".join(self.todos))
        lines.append("（细节见原始消息 ID: " + ",".join(map(str, self.compressed_from_message_ids)) + "）")
        return "\n".join(lines)


_KEYWORDS_CONSTRAINT = ("必须", "要附", "来源", "约束", "不能", "禁止")
_KEYWORDS_TODO = ("待办", "下一步", "还需要", "待完成")
_KEYWORDS_DECISION = ("决定", "采用", "确认", "选定", "方案")


def compress_messages(messages: list[Message]) -> ConversationSummary:
    """规则压缩（离线默认）；保留消息 id 以便回查原话。"""
    summary = ConversationSummary(
        compressed_from_message_ids=[m.id for m in messages],
    )
    user_texts = [m.content for m in messages if m.role == "user"]
    if user_texts:
        summary.goal = user_texts[0][:200]
    for m in messages:
        c = m.content
        if any(k in c for k in _KEYWORDS_CONSTRAINT):
            summary.constraints.append(c[:120])
        elif any(k in c for k in _KEYWORDS_DECISION):
            summary.decisions.append(c[:120])
        elif m.role == "tool" or "完成" in c or "已" in c:
            summary.progress.append(f"{m.role}: {c[:80]}")
        elif any(k in c for k in _KEYWORDS_TODO):
            summary.todos.append(c[:120])
    # 去重
    summary.constraints = list(dict.fromkeys(summary.constraints))[:5]
    summary.decisions = list(dict.fromkeys(summary.decisions))[:5]
    summary.progress = list(dict.fromkeys(summary.progress))[:8]
    summary.todos = list(dict.fromkeys(summary.todos))[:5]
    return summary


def compress_with_llm(messages: list[Message]) -> ConversationSummary | None:
    """可选 LLM 压缩；失败返回 None。"""
    import json as json_mod

    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    from agent_memory.config import Settings

    settings = Settings.load()
    if not settings.openai_api_key or not messages:
        return None
    transcript = "\n".join(f"{m.role}: {m.content}" for m in messages[-40:])
    prompt = (
        "将以下对话压缩为 JSON："
        '{"goal":"","constraints":[],"decisions":[],"progress":[],"todos":[]}'
        f"\n\n{transcript}"
    )
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        raw = llm.invoke(
            [
                SystemMessage(content="只输出 JSON，中文内容。"),
                HumanMessage(content=prompt),
            ]
        )
        text = raw.content if isinstance(raw.content, str) else str(raw.content)
        text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
        data = json_mod.loads(text)
        s = ConversationSummary(
            goal=str(data.get("goal", "")),
            constraints=list(data.get("constraints", [])),
            decisions=list(data.get("decisions", [])),
            progress=list(data.get("progress", [])),
            todos=list(data.get("todos", [])),
            compressed_from_message_ids=[m.id for m in messages],
        )
        return s
    except Exception:
        return None


def maybe_compress(
    all_messages: list[Message],
    recent_n: int,
    threshold: int,
    *,
    use_llm: bool = False,
) -> tuple[ConversationSummary | None, list[Message]]:
    """超过 threshold 时压缩早期消息，保留 recent_n 条原文。"""
    if len(all_messages) <= threshold:
        return None, all_messages[-recent_n:]
    early = all_messages[: -recent_n]
    recent = all_messages[-recent_n:]
    summary = None
    if use_llm:
        summary = compress_with_llm(early)
    if summary is None:
        summary = compress_messages(early)
    return summary, recent