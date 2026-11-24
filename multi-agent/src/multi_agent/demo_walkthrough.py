"""11 步演示，对照 docx/01–11。"""
from __future__ import annotations

import typer

app = typer.Typer()

STEPS = [
    ("01", "execution-protocol-overview", "ma-demo figure-01"),
    ("02", "refund-response-lost-timeout", "ma-demo figure-02"),
    ("03", "model-proposes-system-decides", "pytest tests/test_gateway_t03.py -q"),
    ("04", "business-key-not-task-id", "pytest tests/test_figure04_business_key.py -q"),
    ("05", "unknown-formal-state", "pytest tests/test_state_machine.py -q"),
    ("06", "outbox-task-and-event", "pytest tests/test_outbox.py -q"),
    ("07", "lease-fencing-old-worker", "pytest tests/test_fencing.py -q"),
    ("08", "refund-timeout-query-first", "pytest tests/test_figure08_needs_review.py -q"),
    ("09", "dag-and-tool-gateway-gates", "pytest tests/test_gateway_gates.py -q"),
    ("10", "kafka-lag-vs-task-backlog", "pytest -m metrics -q"),
    ("11", "migration-four-steps", "python scripts/fault_drill/run_all.py"),
]


@app.command()
def walkthrough() -> None:
    """打印 11 图与建议命令（不逐一执行外部进程）。"""
    typer.echo("Multi-Agent 十一图 walkthrough（见 docx/）\n")
    for num, slug, cmd in STEPS:
        typer.echo(f"  [{num}] docx/{num}-{slug}.jpg")
        typer.echo(f"      → {cmd}\n")


def main() -> None:
    app()


if __name__ == "__main__":
    main()