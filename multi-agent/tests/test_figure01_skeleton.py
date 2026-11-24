"""图 01 — 可恢复执行协议 E2E 骨架（矩阵 §01 验收）。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from multi_agent.domain import TaskStatus, WorkflowStatus
from multi_agent.e2e_skeleton import run_figure01_happy_path
from multi_agent.engine import SupervisorEngine
from multi_agent.payment.client import PaymentClient
from multi_agent.payment.server import reset_state
from multi_agent.store import Store


@pytest.fixture
def figure01_engine():
    reset_state()
    store = Store(":memory:")
    return store, SupervisorEngine(store, PaymentClient("asgi://payment"))


@pytest.mark.figure01
def test_figure01_supervisor_creates_refund_and_coupon_tasks(figure01_engine):
    store, engine = figure01_engine
    wf = engine.start_case()
    steps = {t.logical_step_key: t for t in store.list_tasks(wf)}
    assert len(steps) == 2
    assert steps["refund"].status == TaskStatus.READY
    assert steps["coupon"].status == TaskStatus.WAITING
    assert steps["coupon"].depends_on_task_id == steps["refund"].id
    assert store.get_workflow_status(wf) == WorkflowStatus.RUNNING


@pytest.mark.figure01
def test_figure01_e2e_skeleton_happy_path(figure01_engine):
    _, engine = figure01_engine
    result = run_figure01_happy_path(engine)
    assert result.refund_succeeded
    assert result.coupon_succeeded
    assert result.refund_status == TaskStatus.SUCCEEDED
    assert result.coupon_status == TaskStatus.SUCCEEDED
    assert result.payment_post_count == 1
    assert _outbox_has_workflow(engine, result.workflow_id)


def _outbox_has_workflow(engine: SupervisorEngine, wf: str) -> bool:
    row = engine.store._conn.execute(
        "SELECT COUNT(*) c FROM outbox_events WHERE aggregate_id=? OR payload_json LIKE ?",
        (wf, f"%{wf}%"),
    ).fetchone()
    return int(row["c"]) >= 1


@pytest.mark.figure01
def test_figure01_engine_run_full_happy_path_alias(figure01_engine):
    _, engine = figure01_engine
    result = engine.run_full_happy_path()
    assert result.refund_status == TaskStatus.SUCCEEDED


@pytest.mark.figure01
def test_figure01_k8s_manifests_dry_run_client():
    root = Path(__file__).resolve().parents[1]
    k8s = root / "deploy" / "k8s"
    manifests = list(k8s.glob("*.yaml"))
    assert len(manifests) >= 2
    if not _kubectl_available():
        pytest.skip("kubectl not installed")
    for path in manifests:
        subprocess.run(
            ["kubectl", "apply", "--dry-run=client", "-f", str(path)],
            check=True,
            capture_output=True,
        )


def _kubectl_available() -> bool:
    try:
        subprocess.run(
            ["kubectl", "version", "--client=true"],
            check=True,
            capture_output=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False