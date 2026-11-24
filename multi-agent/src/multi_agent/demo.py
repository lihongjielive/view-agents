"""Typer 演示入口（ma-demo）：按 docx 图号跑 E2E / 故障片段。

每个子命令对应 tests/test_figure*.py 或 e2e_*.py 的同一路径。
"""
from __future__ import annotations

import typer

from multi_agent.engine import SupervisorEngine
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.store import Store

app = typer.Typer()


@app.command("figure-01")
def figure_01() -> None:
    """图 01：协议总览 E2E 骨架（Supervisor + 双 Worker + 支付 Mock）。"""
    from multi_agent.e2e_skeleton import run_figure01_happy_path

    reset_state()
    store = Store(":memory:")
    engine = SupervisorEngine(store, PaymentClient("asgi://payment"))
    result = run_figure01_happy_path(engine)
    typer.echo(
        f"workflow={result.workflow_id} "
        f"refund={result.refund_status.value} "
        f"coupon={result.coupon_status.value} "
        f"posts={result.payment_post_count}"
    )


@app.command("figure-02")
def figure_02() -> None:
    """图 02：响应丢失、超时≠失败、查询后收敛。"""
    from multi_agent.e2e_figure02 import run_figure02_response_lost

    reset_state()
    store = Store(":memory:")
    engine = SupervisorEngine(store, PaymentClient("asgi://payment"))
    result = run_figure02_response_lost(engine)
    typer.echo(
        f"refund={result.refund_status.value} coupon={result.coupon_status.value} "
        f"posts={result.payment_post_count}"
    )


@app.command()
def happy() -> None:
    reset_state()
    store = Store(":memory:")
    engine = SupervisorEngine(store, PaymentClient("asgi://payment"))
    wf = engine.start_case()
    engine.run_refund_workflow(wf)
    engine.run_coupon(wf)
    tasks = {t.logical_step_key: t.status.value for t in store.list_tasks(wf)}
    typer.echo(f"tasks={tasks}")


@app.command()
def timeout_reconcile() -> None:
    reset_state()
    pay = PaymentClient("asgi://payment")
    pay.set_fault("drop_response_after_success")
    store = Store(":memory:")
    engine = SupervisorEngine(store, pay)
    wf = engine.start_case()
    engine.run_refund_workflow(wf)
    posts = store.count_http_posts_to_payment()
    coupon = next(t for t in store.list_tasks(wf) if t.logical_step_key == "coupon")
    refund = next(t for t in store.list_tasks(wf) if t.logical_step_key == "refund")
    typer.echo(f"refund={refund.status.value} coupon={coupon.status.value} posts={posts}")
    pay.clear_fault()
    engine.reconcile_refund(wf)
    engine.run_coupon(wf)
    tasks = {t.logical_step_key: t.status.value for t in store.list_tasks(wf)}
    typer.echo(f"after reconcile tasks={tasks} posts={store.count_http_posts_to_payment()}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()