"""可选：对接 agent-memory 四路记忆（AGENT_KIT_USE_COORDINATOR=1）。"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_memory.coordinator import MemoryCoordinator


def coordinator_enabled() -> bool:
    return os.getenv("AGENT_KIT_USE_COORDINATOR", "").lower() in (
        "1",
        "true",
        "yes",
    )


def try_load_coordinator() -> MemoryCoordinator | None:
    if not coordinator_enabled():
        return None
    try:
        from agent_memory.coordinator import MemoryCoordinator
    except ImportError:
        return None
    return MemoryCoordinator()


def build_planner_context(
    coordinator: MemoryCoordinator,
    session_id: str,
    user_id: str,
    goal: str,
) -> str:
    ctx = coordinator.build_context(
        session_id,
        user_id,
        task_hint=goal,
        retrieval_query=goal,
    )
    return ctx.full_text


def sync_user_turn(
    coordinator: MemoryCoordinator, session_id: str, goal: str
) -> None:
    coordinator.session.append_message(session_id, "user", goal)
    coordinator.persona.ingest_user_message(
        os.getenv("AGENT_KIT_USER_ID", "default-user"), goal
    )