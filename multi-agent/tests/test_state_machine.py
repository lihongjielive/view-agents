"""图 05 — 状态机。"""
from __future__ import annotations

import pytest

from multi_agent.domain import TaskStatus, WorkflowStatus
from multi_agent.state_machine import (
    assert_task_transition,
    assert_workflow_transition,
)


@pytest.mark.figure05
def test_task_unknown_is_valid():
    assert_task_transition(TaskStatus.RUNNING, TaskStatus.UNKNOWN)


@pytest.mark.figure05
def test_workflow_needs_review_from_running():
    assert_workflow_transition(WorkflowStatus.RUNNING, WorkflowStatus.NEEDS_REVIEW)


def test_task_illegal_transition_raises():
    with pytest.raises(ValueError):
        assert_task_transition(TaskStatus.SUCCEEDED, TaskStatus.RUNNING)