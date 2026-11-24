"""图 03/09 — Gateway 表驱动扩展。"""
from __future__ import annotations

import pytest

from multi_agent.domain import TaskStatus, WorkflowStatus
from multi_agent.gateway import Proposal, ToolGateway
from multi_agent.proposals import submit_proposal
from multi_agent.store import Store


def _gw_case():
    store = Store(":memory:")
    wf = store.create_workflow(tenant="T1", order_id="O", after_sale_id="A", refund_amount=1.0)
    gw = ToolGateway(store)
    return store, wf, gw


@pytest.mark.parametrize(
    "patch,expect_code",
    [
        ({"approval_snapshot_id": "wrong"}, "T03_APPROVAL"),
        ({"tenant": "T2"}, "T03_TENANT"),
        ({"amount": -1}, "T03_FACT"),
        ({"access_token": "bad"}, "T09_TOKEN"),
        ({"amount": 99_999}, "T03_QUOTA"),
    ],
)
@pytest.mark.gate09
def test_gateway_rejections(patch, expect_code):
    _, wf, gw = _gw_case()
    base = dict(
        tenant="T1",
        tool="refund.create",
        order_id="O",
        after_sale_id="A",
        amount=10.0,
        actor="t",
        approval_snapshot_id="appr-default",
    )
    base.update(patch)
    d = submit_proposal(gw, wf, Proposal(**base)).decision
    assert d.code == expect_code
    assert not d.allow


@pytest.mark.gate09
def test_needs_review_blocks_proposal():
    store, wf, gw = _gw_case()
    store.set_workflow_status(wf, WorkflowStatus.NEEDS_REVIEW)
    d = submit_proposal(
        gw,
        wf,
        Proposal(
            tenant="T1",
            tool="refund.create",
            order_id="O",
            after_sale_id="A",
            amount=1.0,
            actor="t",
            approval_snapshot_id="appr-default",
        ),
    ).decision
    assert d.code == "T03_REVIEW"


@pytest.mark.gate09
def test_dag_dep_when_refund_not_succeeded():
    store, wf, gw = _gw_case()
    d = submit_proposal(
        gw,
        wf,
        Proposal(
            tenant="T1",
            tool="coupon.issue",
            order_id="O",
            after_sale_id="A",
            amount=5.0,
            actor="t",
            approval_snapshot_id="appr-default",
        ),
    ).decision
    assert d.code == "T03_DEP"