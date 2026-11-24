"""CLI 呈现层：图示「自然语言输出」+ thread 级历史（MemorySaver）。"""
from __future__ import annotations

import os
import uuid

import typer
from langchain_core.messages import AIMessage

from agent.config import load_project_env

from agent.agent_framework import default_agent
from agent.graph import build_graph


app = typer.Typer(help="LangGraph Agent CLI (LLM + tools loop)")


def _thread_config(thread_id: str) -> dict:
    """LangGraph configurable：同 thread_id 共享 checkpoint 历史。"""
    return {"configurable": {"thread_id": thread_id}}


def _last_ai_text(messages: list) -> str:
    """取最后一条有文本的 AIMessage 作为终答展示。"""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content:
            text = m.content if isinstance(m.content, str) else str(m.content)
            if text.strip():
                return text
    return "(no assistant message)"


@app.command()
def run(
    # typer.Argument → 位置参数；
    task: str = typer.Argument(..., help="User task / question"),
    # typer.Option → --xxx / -x 选项
    thread: str = typer.Option("default", "--thread", "-t", help="Checkpoint thread id"),
    # verbose 是 agent run 命令里的一个开关（-v / --verbose），用来决定执行图时要不要把每个节点跑过并更新了哪些状态字段打到终端上
        # False（默认）： 执行方式：graph.invoke(...) 一次跑完； graph.invoke(...) 一次跑完
        # True： 执行方式： graph.stream(..., stream_mode="updates")； 每个节点一行
    verbose: bool = typer.Option(True, "--verbose", "-v", help="Print node steps"),
) -> None:
    """单轮任务：初始化 State 后 invoke 整条图直至 END。"""
    load_project_env()
    if not os.getenv("OPENAI_API_KEY"):
        typer.echo("Set OPENAI_API_KEY in .env or environment.", err=True)
        raise typer.Exit(1)

    graph = build_graph(default_agent())
    config = _thread_config(thread)
    # 与 AgentState 字段对应；messages 空列表由 add_messages 归约增长
    inputs = {"input": task, "messages": [], "intermediate_steps": [], "flags": {}}

    if verbose:
        # stream_mode=updates：按节点打印局部更新，便于对照图示流程
        for event in graph.stream(inputs, config, stream_mode="updates"):
            for node, payload in event.items():
                typer.echo(f"[{node}] {list(payload.keys())}")
        result = graph.get_state(config).values
    else:
        result = graph.invoke(inputs, config)

    typer.echo(_last_ai_text(result.get("messages") or []))


@app.command()
def chat(
    thread: str = typer.Option("default", "--thread", "-t"),
) -> None:
    """多轮对话：每轮只传 input，历史由 checkpointer 自动并入。"""
    load_project_env()
    if not os.getenv("OPENAI_API_KEY"):
        typer.echo("Set OPENAI_API_KEY in .env or environment.", err=True)
        raise typer.Exit(1)

    graph = build_graph(default_agent())
    config = _thread_config(thread)
    # typer.echo 是 Typer 提供的向终端输出文字 的方法，作用上接近 print()，但更适合写命令行程序。
    typer.echo(f"Thread: {thread}. Type 'exit' to quit.")

    while True:
        try:
            line = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line or line.lower() in {"exit", "quit"}:
            break
        graph.invoke({"input": line}, config)
        state = graph.get_state(config).values
        typer.echo(f"Agent> {_last_ai_text(state.get('messages') or [])}")


@app.command()
def new_thread() -> None:
    """输出新 UUID，用于隔离会话 checkpoint。"""
    typer.echo(str(uuid.uuid4()))


# 装饰器对比（本项目）
#    装饰器                      库                      作用
# @app.command()               Typer                   CLI 子命令
# @app.get / @app.post       FastAPI（api.py）          HTTP 路由
# @tool                        LangChain               注册 LLM 工具
# @dataclass                   标准库                   数据类

if __name__ == "__main__":
    app()