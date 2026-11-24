"""Slide 11: fault drills (pytest entry)."""
from __future__ import annotations

import pytest

from multi_agent.fault_drill import (
    run_crash_before_offset,
    run_late_callback,
    run_lost_publish_ack,
    run_success_response_lost,
    run_worker_disconnect,
)

DRILLS = [
    ("lost_publish_ack", run_lost_publish_ack),
    ("crash_before_offset", run_crash_before_offset),
    ("worker_disconnect", run_worker_disconnect),
    ("success_response_lost", run_success_response_lost),
    ("late_callback", run_late_callback),
]


@pytest.mark.fault_drill
@pytest.mark.parametrize("name,fn", DRILLS, ids=[d[0] for d in DRILLS])
def test_fault_drill(name: str, fn):
    result = fn()
    assert result is not None


def test_fault_drill_run_all():
    """Meta: all drills green in one shot (CI)."""
    for _name, fn in DRILLS:
        fn()