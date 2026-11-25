"""组合四种记忆，组装下一次调用的上下文。"""
from __future__ import annotations

from dataclasses import dataclass

from agent_memory.compression import ConversationSummary, maybe_compress
from agent_memory.config import Settings
from agent_memory.persona import PersonaStore
from agent_memory.session import SessionStore
from agent_memory.vector_memory import VectorMemory


@dataclass
class AssembledContext:
    session_id: str
    user_id: str
    summary: ConversationSummary | None
    recent_dialogue: str
    persona_block: str
    retrieval_block: str
    checkpoint_block: str
    full_text: str


class MemoryCoordinator:
    def __init__(
        self,
        session: SessionStore | None = None,
        persona: PersonaStore | None = None,
        vectors: VectorMemory | None = None,
    ) -> None:
        self.session = session or SessionStore()
        self.persona = persona or PersonaStore()
        self.vectors = vectors or VectorMemory()
        self.settings = Settings.load()

    def build_context(
        self,
        session_id: str,
        user_id: str,
        task_hint: str = "",
        retrieval_query: str = "",
        *,
        use_llm_compress: bool = False,
    ) -> AssembledContext:
        cfg = self.settings.raw
        recent_n = int(cfg.get("session", {}).get("recent_turns", 6))
        threshold = int(cfg.get("session", {}).get("compress_after_turns", 12))
        all_msgs = self.session.list_messages(session_id)
        summary, recent = maybe_compress(
            all_msgs, recent_n, threshold, use_llm=use_llm_compress
        )
        recent_lines = [f"{m.role}: {m.content}" for m in recent]
        recent_dialogue = "\n".join(recent_lines)

        facts = self.persona.facts_for_task(user_id, task_hint)
        persona_lines = [f"- {f.content}（更新 {f.updated_at[:10]}）" for f in facts]
        persona_block = "【用户画像】\n" + ("\n".join(persona_lines) if persona_lines else "（无）")

        query = retrieval_query or task_hint or (recent[-1].content if recent else "")
        hits = self.vectors.retrieve(query) if query else []
        ret_lines = [f"- [{s:.2f}] {c.text}" for s, c in hits]
        retrieval_block = "【检索片段】\n" + ("\n".join(ret_lines) if ret_lines else "（无）")

        cps = self.session.list_checkpoints(session_id)
        cp_lines = [f"- {c.step}: {c.status.value} — {c.description}" for c in cps]
        checkpoint_block = "【任务检查点】\n" + (
            "\n".join(cp_lines) if cp_lines else "（无）"
        )

        parts: list[str] = []
        if summary:
            parts.append(summary.to_text())
        parts.append("【近期对话】\n" + recent_dialogue)
        parts.append(persona_block)
        parts.append(retrieval_block)
        parts.append(checkpoint_block)
        full_text = "\n\n".join(parts)
        return AssembledContext(
            session_id=session_id,
            user_id=user_id,
            summary=summary,
            recent_dialogue=recent_dialogue,
            persona_block=persona_block,
            retrieval_block=retrieval_block,
            checkpoint_block=checkpoint_block,
            full_text=full_text,
        )