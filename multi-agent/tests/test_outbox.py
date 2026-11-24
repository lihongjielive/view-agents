"""图 06 — Outbox 专项。"""
from __future__ import annotations

import pytest

from multi_agent.outbox import OutboxPipeline
from multi_agent.store import Store


@pytest.mark.outbox
def test_outbox_same_transaction_as_workflow_create():
    store = Store(":memory:")
    store.create_workflow(tenant="T1", order_id="O", after_sale_id="A", refund_amount=1.0)
    assert store.count_unpublished_outbox() >= 1


@pytest.mark.outbox
def test_publish_ack_loss_then_retry():
    store = Store(":memory:")
    store.create_workflow(tenant="T1", order_id="O2", after_sale_id="A2", refund_amount=1.0)
    pipe = OutboxPipeline(store)
    pipe.publish_pending(simulate_ack_loss=True)
    assert store.count_unpublished_outbox() >= 1
    pipe.publish_pending(simulate_ack_loss=False)
    assert store.count_unpublished_outbox() == 0


@pytest.mark.outbox
def test_ingest_idempotent_on_replay():
    store = Store(":memory:")
    store.create_workflow(tenant="T1", order_id="O3", after_sale_id="A3", refund_amount=1.0)
    pipe = OutboxPipeline(store)
    pipe.publish_pending()
    assert pipe.ingest_all() >= 1
    assert pipe.ingest_all() == 0