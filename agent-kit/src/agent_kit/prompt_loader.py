"""读取 prompts/*.md 与 task 模板渲染。"""
from __future__ import annotations

from pathlib import Path

from agent_kit.config import Settings


def load_prompt(relative: str, settings: Settings | None = None) -> str:
    settings = settings or Settings.load()
    path = settings.root / relative
    return path.read_text(encoding="utf-8")


def render_task(goal: str, context: str = "", max_steps: int = 6) -> str:
    settings = Settings.load()
    tpl = load_prompt("prompts/task.md", settings)
    return (
        tpl.replace("{{goal}}", goal)
        .replace("{{context}}", context or "（无）")
        .replace("{{max_steps}}", str(max_steps))
    )