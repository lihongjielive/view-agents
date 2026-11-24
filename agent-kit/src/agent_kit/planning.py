"""规划：将目标拆为可执行步骤。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StepKind(str, Enum):
    TOOL = "tool"
    SKILL = "skill"
    MCP = "mcp"


@dataclass
class PlanStep:
    index: int
    description: str
    kind: StepKind
    target: str
    arguments: dict


def plan_demo(goal: str) -> list[PlanStep]:
    """规则规划（离线教学默认）。"""
    lower = goal.lower()
    steps: list[PlanStep] = []
    n = 1
    if any(k in goal for k in ("天气", "搜索", "查询", "北京")):
        steps.append(
            PlanStep(
                n,
                "检索外部信息",
                StepKind.TOOL,
                "search",
                {"query": goal},
            )
        )
        n += 1
    if any(k in lower for k in ("csv", "分析", "数据", "趋势")):
        steps.append(
            PlanStep(
                n,
                "数据分析管道",
                StepKind.SKILL,
                "data_analysis",
                {"goal": goal},
            )
        )
        n += 1
        steps.append(
            PlanStep(
                n,
                "生成报告",
                StepKind.SKILL,
                "report_generation",
                {},
            )
        )
        n += 1
    if any(k in goal for k in ("计算", "+", "求和", "多少")):
        steps.append(
            PlanStep(
                n,
                "数值计算",
                StepKind.TOOL,
                "calculator",
                {"expression": "1+1"},
            )
        )
        n += 1
    if not steps:
        steps.append(
            PlanStep(
                1,
                "MCP 探活",
                StepKind.MCP,
                "mcp_ping",
                {},
            )
        )
        steps.append(
            PlanStep(
                2,
                "生成摘要",
                StepKind.SKILL,
                "report_generation",
                {"title": "执行摘要"},
            )
        )
    return steps


def _parse_plan_json(data: object) -> list[PlanStep] | None:
    if not isinstance(data, dict):
        return None
    steps_raw = data.get("steps")
    if not isinstance(steps_raw, list):
        return None
    steps: list[PlanStep] = []
    for i, raw in enumerate(steps_raw, start=1):
        if not isinstance(raw, dict):
            return None
        kind_str = str(raw.get("kind", "tool")).lower()
        try:
            kind = StepKind(kind_str)
        except ValueError:
            kind = StepKind.TOOL
        target = str(raw.get("target", ""))
        if not target:
            return None
        args = raw.get("arguments")
        if not isinstance(args, dict):
            args = {}
        steps.append(
            PlanStep(
                index=int(raw.get("index", i)),
                description=str(raw.get("description", target)),
                kind=kind,
                target=target,
                arguments=args,
            )
        )
    return steps or None


def plan_with_llm(goal: str, context: str = "") -> list[PlanStep]:
    """LLM 规划；失败回落 plan_demo。"""
    import json

    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    from agent_kit.config import Settings
    from agent_kit.prompt_loader import load_prompt, render_task

    settings = Settings.load()
    if not settings.openai_api_key:
        return plan_demo(goal)

    system = load_prompt("prompts/system.md")
    task = render_task(goal, context)
    schema_hint = (
        '只返回 JSON：{"steps":[{"index":1,"description":"...","kind":"tool|skill|mcp",'
        '"target":"search|calculator|data_analysis|mcp_ping|...","arguments":{}}]}'
    )
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=float(settings.raw.get("llm", {}).get("temperature", 0.2)),
    )
    try:
        msg = llm.invoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=f"{task}\n\n{schema_hint}"),
            ]
        )
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        data = json.loads(content)
        parsed = _parse_plan_json(data)
        if parsed:
            return parsed
    except Exception:
        pass
    return plan_demo(goal)


def resolve_plan(goal: str, context: str = "", *, use_llm: bool = False) -> list[PlanStep]:
    if use_llm:
        return plan_with_llm(goal, context)
    return plan_demo(goal)