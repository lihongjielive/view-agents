"""CLI（ma-langgraph-poc）：跑通 propose→execute 固定图，输出 workflow 与裁决码。"""
from __future__ import annotations

import typer

from multi_agent.domain import TaskStatus
from multi_agent.langgraph_poc.graph import run_poc_case

app = typer.Typer(help="LangGraph propose-only PoC wired to multi_agent execution")


@app.command()
def run(
    order_id: str = typer.Option("ORD-LG-CLI", "--order"),
    after_sale_id: str = typer.Option("AS-LG-CLI", "--after-sale"),
) -> None:
    out = run_poc_case(order_id=order_id, after_sale_id=after_sale_id)
    typer.echo(
        f"workflow={out.get('workflow_id')} "
        f"refund={out.get('refund_executed')} coupon={out.get('coupon_executed')} "
        f"codes={out.get('refund_proposal_code')}/{out.get('coupon_proposal_code')}"
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()