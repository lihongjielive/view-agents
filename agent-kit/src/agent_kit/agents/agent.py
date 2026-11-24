"""智能体：规划 + 记忆 + 工具/技能 + MCP。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from agent_kit.config import Settings, load_agent_yaml
from agent_kit.memory.base import SQLiteMemory
from agent_kit.memory.vector_store import InMemoryVectorStore
from agent_kit.mcp_client import McpClient
from agent_kit.planning import PlanStep, StepKind, resolve_plan
from agent_kit.prompt_loader import load_prompt, render_task
from agent_kit.skills import SKILL_REGISTRY
from agent_kit.tools import TOOL_REGISTRY


@dataclass
class AgentRunResult:
    goal: str
    plan: list[PlanStep]
    observations: list[dict[str, Any]] = field(default_factory=list)
    report: dict[str, Any] | None = None


def _index_examples(vectors: InMemoryVectorStore, settings: Settings) -> None:
    text = load_prompt("prompts/examples.md", settings)
    chunks = re.split(r"(?=^### )", text, flags=re.MULTILINE)
    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if chunk:
            vectors.add(chunk, doc_id=f"example-{i}")


class KitAgent:
    def __init__(self, memory: SQLiteMemory | None = None) -> None:
        self.spec = load_agent_yaml()
        self.settings = Settings.load()
        self.memory = memory or SQLiteMemory()
        self.vectors = InMemoryVectorStore()
        system = load_prompt(self.spec["prompts"]["system"])
        self.vectors.add(system, doc_id="system-prompt")
        _index_examples(self.vectors, self.settings)

    def memory_search(self, query: str, k: int = 3) -> list[str]:
        return [rec.text for score, rec in self.vectors.search(query, k=k) if score > 0]

    def run(
        self,
        goal: str,
        *,
        mcp_offline: bool = True,
        use_llm: bool = False,
    ) -> AgentRunResult:
        self.memory.add_turn("user", goal)
        session_ctx = self.memory.session_context()
        retrieved = self.memory_search(goal, k=2)
        extra = "\n".join(retrieved)
        context = f"{session_ctx}\n\n检索示例:\n{extra}".strip()
        max_steps = int(self.settings.raw.get("llm", {}).get("max_plan_steps", 6))
        _ = render_task(goal, context, max_steps=max_steps)
        plan = resolve_plan(goal, context, use_llm=use_llm)
        mcp = McpClient(offline=mcp_offline)
        observations: list[dict[str, Any]] = []
        last_analysis: dict | None = None

        for step in plan:
            if step.kind == StepKind.TOOL:
                fn = TOOL_REGISTRY.get(step.target)
                if not fn:
                    out = {"error": "unknown_tool", "name": step.target}
                else:
                    out = fn(**step.arguments)
            elif step.kind == StepKind.SKILL:
                fn = SKILL_REGISTRY.get(step.target)
                if not fn:
                    out = {"error": "unknown_skill", "name": step.target}
                else:
                    if step.target == "data_analysis":
                        last_analysis = fn(**step.arguments)
                        out = last_analysis
                    elif step.target == "report_generation":
                        sections = [
                            {"heading": s.description, "body": o}
                            for s, o in zip(plan, observations)
                        ]
                        out = fn(
                            analysis=last_analysis,
                            sections=sections,
                            **step.arguments,
                        )
                    else:
                        out = fn(**step.arguments)
            else:
                out = mcp.call(step.target, step.arguments)

            observations.append({"step": step.index, "target": step.target, "output": out})
            self.memory.add_turn("assistant", f"{step.target}: {out!s}")

        report = None
        if observations:
            last = observations[-1].get("output")
            if isinstance(last, dict) and last.get("format") == "markdown":
                report = last

        return AgentRunResult(goal=goal, plan=plan, observations=observations, report=report)