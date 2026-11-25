"""agent-memory CLI：演示四种记忆。"""
from __future__ import annotations

import sys

import typer

from agent_memory.coordinator import MemoryCoordinator
from agent_memory.persona import PersonaStore
from agent_memory.session import SessionStore, StepStatus
from agent_memory.vector_memory import VectorMemory

app = typer.Typer(help="Agent 四种记忆：会话 / 压缩 / 画像 / 向量")


@app.command("demo-report")
def demo_report(user_id: str = "user-001") -> None:
    """模拟报告任务：写入四路记忆并输出组装上下文。"""
    coord = MemoryCoordinator()
    sid = coord.session.create_session(topic="产品调研报告")
    coord.session.append_message(sid, "user", "我要写一份市场调研报告，必须附来源")
    coord.persona.ingest_user_message(user_id, "以后写报告要附来源")
    coord.vectors.add_chunk(
        "项目目标：提升用户留存，曾比较方案 A 与 B，最终选定方案 A。",
        project="report-2024",
    )
    coord.vectors.add_chunk(
        "交付要求：下迭代前完成核心功能。",
        project="report-2024",
    )
    coord.session.set_checkpoint(
        sid, "collect_data", StepStatus.COMPLETED, "已收集资料"
    )
    coord.session.set_checkpoint(
        sid, "add_citations", StepStatus.IN_PROGRESS, "正在添加引用"
    )
    coord.session.set_checkpoint(
        sid, "export_pdf", StepStatus.PENDING, "等待导出"
    )
    for i in range(14):
        coord.session.append_message(
            sid, "assistant", f"中间步骤说明 #{i + 1}：继续完善报告正文"
        )
    coord.session.append_message(sid, "user", "继续添加引用")
    coord.session.append_message(sid, "tool", "找到 3 条来源：白皮书、研报、新闻")
    ctx = coord.build_context(
        sid, user_id, task_hint="写项目报告", retrieval_query="上次如何决定方案"
    )
    typer.echo(ctx.full_text)


@app.command("build-context")
def build_context_cmd(
    session_id: str = typer.Argument(...),
    user_id: str = typer.Option("user-001", "--user"),
    task: str = typer.Option("", "--task"),
    query: str = typer.Option("", "--query"),
    llm_compress: bool = typer.Option(False, "--llm-compress"),
) -> None:
    ctx = MemoryCoordinator().build_context(
        session_id,
        user_id,
        task_hint=task,
        retrieval_query=query,
        use_llm_compress=llm_compress,
    )
    typer.echo(ctx.full_text)


@app.command("session-resume")
def session_resume(
    session_id: str = typer.Argument(...),
    user_id: str = typer.Option("user-001", "--user"),
) -> None:
    """中断后恢复：检查点 + 组装上下文。"""
    store = SessionStore()
    cps = store.list_checkpoints(session_id)
    active = [c for c in cps if c.status == StepStatus.IN_PROGRESS]
    typer.echo("=== 检查点 ===")
    for c in cps:
        typer.echo(f"  {c.step}: {c.status.value} — {c.description}")
    if active:
        typer.echo(f"\n当前步骤: {active[0].step}")
    typer.echo("\n=== 组装上下文 ===\n")
    ctx = MemoryCoordinator().build_context(session_id, user_id)
    typer.echo(ctx.full_text)


@app.command("ingest-chunk")
def ingest_chunk(
    text: str = typer.Argument(...),
    project: str = typer.Option("default", "--project"),
) -> None:
    cid = VectorMemory().add_chunk(text, project=project)
    typer.echo(f"chunk_id={cid} project={project}")


@app.command("persona-list")
def persona_list(
    user_id: str = typer.Argument(...),
    task: str = typer.Option("", "--task"),
) -> None:
    facts = PersonaStore().facts_for_task(user_id, task)
    for f in facts:
        typer.echo(f"[{f.fact_key}] {f.content} (更新 {f.updated_at[:10]})")


@app.command("get-message")
def get_message(message_id: int) -> None:
    """回查摘要丢失的原话。"""
    msg = SessionStore().get_message(message_id)
    if not msg:
        typer.echo("未找到", err=True)
        raise typer.Exit(1)
    typer.echo(f"[{msg.id}] {msg.role}: {msg.content}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("demo-report")
    app(prog_name="agent-memory")