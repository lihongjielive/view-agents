"""CLI：agent-kit run | analyze | mcp-* | refund-demo | memory-search"""
from __future__ import annotations

import json
from pathlib import Path

import typer

from agent_kit.agents.agent import KitAgent
from agent_kit.agents.data_analysis_agent import AnalysisTask, DataAnalysisAgent, TaskType
from agent_kit.config import Settings, load_agent_yaml
from agent_kit.mcp_bridge import mcp_tools_call
from agent_kit.mcp_client import McpClient
from agent_kit.refund_demo import run_refund_demo

app = typer.Typer(add_completion=False, help="0→1 Agent 骨架 CLI")


@app.command("init-info")
def init_info() -> None:
    """打印教材 8 步对应的目录（等同 codex init my-agent 自检）。"""
    root = Settings.load().root
    typer.echo(f"项目根: {root}")
    for name in ("agents", "skills", "tools", "memory", "prompts"):
        typer.echo(f"  [{name}] -> {root / name if name != 'tools' else 'src/agent_kit/tools'}")
    spec = load_agent_yaml()
    typer.echo(f"默认 Agent: {spec.get('id')} — {spec.get('name')}")
    typer.echo(f"契约: {Settings.load().socket_contract_path}")


@app.command("run")
def run_demo(
    goal: str = typer.Argument("查询北京天气并给出旅行建议"),
    mcp_live: bool = typer.Option(False, "--mcp-live", help="真实请求 MCP HTTP"),
    llm: bool = typer.Option(False, "--llm", help="使用 LLM 规划（需 OPENAI_API_KEY）"),
) -> None:
    if llm and not Settings.load().openai_api_key:
        typer.echo("错误: --llm 需要设置 OPENAI_API_KEY", err=True)
        raise typer.Exit(code=1)
    agent = KitAgent()
    result = agent.run(goal, mcp_offline=not mcp_live, use_llm=llm)
    typer.echo(f"规划 {len(result.plan)} 步")
    for step in result.plan:
        typer.echo(f"  {step.index}. [{step.kind.value}] {step.target} — {step.description}")
    if result.report and "content" in result.report:
        typer.echo("\n--- 报告 ---\n")
        typer.echo(result.report["content"])


@app.command("analyze")
def analyze_csv(
    csv_path: Path = typer.Argument(..., exists=True, readable=True),
    task_id: str = "TASK-001",
) -> None:
    task = AnalysisTask(
        task_id=task_id,
        task_type=TaskType.EXPLORATION,
        data_source=str(csv_path),
        requirements="探索性分析并输出 Markdown",
    )
    out = DataAnalysisAgent().run(task)
    typer.echo(out["report"])


@app.command("mcp-ping")
def mcp_ping(live: bool = typer.Option(False, "--live")) -> None:
    out = mcp_tools_call("mcp_ping", offline=not live)
    typer.echo(out)


@app.command("mcp-catalog")
def mcp_catalog(
    plug: str | None = typer.Option(None, "--plug", help="core | multi_agent | langgraph"),
    live: bool = typer.Option(False, "--live"),
) -> None:
    client = McpClient(offline=not live)
    typer.echo(json.dumps(client.catalog(plug_id=plug), ensure_ascii=False, indent=2))


@app.command("mcp-describe")
def mcp_describe(
    name: str = typer.Argument(..., help="契约工具名，如 multi_agent_create_workflow"),
    live: bool = typer.Option(False, "--live"),
) -> None:
    client = McpClient(offline=not live)
    typer.echo(json.dumps(client.describe(name), ensure_ascii=False, indent=2))


@app.command("refund-demo")
def refund_demo(
    order_id: str = typer.Argument("ORD-DEMO-001"),
    after_sale_id: str = typer.Argument("AS-DEMO-001"),
    refund_amount: float = typer.Option(88.0, "--amount"),
    live: bool = typer.Option(False, "--live"),
) -> None:
    out = run_refund_demo(
        order_id, after_sale_id, refund_amount, offline=not live
    )
    typer.echo(json.dumps(out, ensure_ascii=False, indent=2))


@app.command("memory-search")
def memory_search_cmd(
    query: str = typer.Argument(..., help="检索 prompts/examples 与 system"),
    k: int = typer.Option(3, "--k"),
) -> None:
    hits = KitAgent().memory_search(query, k=k)
    for i, text in enumerate(hits, 1):
        typer.echo(f"--- hit {i} ---\n{text[:500]}\n")


if __name__ == "__main__":
    app()