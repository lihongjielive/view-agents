"""合法状态迁移表（图 05）；Store / Worker 在写库前必须经 assert_*_transition。

设计要点：
- Task UNKNOWN 可回到多条路径，支持「先查后决」而非直接 FAILED
- Workflow NEEDS_REVIEW 可人工/对账后回到 RUNNING 或终态
- ToolOperation UNKNOWN → CONFIRMED 仅在对账或 GET 成功后
"""
from __future__ import annotations

from multi_agent.domain import TaskStatus, ToolOpStatus, WorkflowStatus

# 图 05：步骤级（含 DAG 中 coupon WAITING → READY）
TASK_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.WAITING: frozenset({TaskStatus.READY}),
    TaskStatus.READY: frozenset({TaskStatus.CLAIMED, TaskStatus.WAITING}),
    TaskStatus.CLAIMED: frozenset({TaskStatus.RUNNING, TaskStatus.READY, TaskStatus.SUCCEEDED}),
    TaskStatus.RUNNING: frozenset(
        {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.UNKNOWN}
    ),
    TaskStatus.UNKNOWN: frozenset(
        {
            TaskStatus.SUCCEEDED,
            TaskStatus.FAILED,
            TaskStatus.RUNNING,
            TaskStatus.READY,
            TaskStatus.CLAIMED,
        }
    ),
    TaskStatus.SUCCEEDED: frozenset(),
    TaskStatus.FAILED: frozenset(),
}

# 工作流级（补偿、需人工复核）
WORKFLOW_TRANSITIONS: dict[WorkflowStatus, frozenset[WorkflowStatus]] = {
    WorkflowStatus.RUNNING: frozenset(
        {
            WorkflowStatus.SUCCEEDED,
            WorkflowStatus.FAILED,
            WorkflowStatus.COMPENSATING,
            WorkflowStatus.NEEDS_REVIEW,
        }
    ),
    WorkflowStatus.COMPENSATING: frozenset(
        {WorkflowStatus.COMPENSATED, WorkflowStatus.NEEDS_REVIEW}
    ),
    WorkflowStatus.SUCCEEDED: frozenset(),
    WorkflowStatus.FAILED: frozenset(),
    WorkflowStatus.COMPENSATED: frozenset(),
    WorkflowStatus.NEEDS_REVIEW: frozenset(
        {WorkflowStatus.RUNNING, WorkflowStatus.FAILED, WorkflowStatus.SUCCEEDED}
    ),
}

# 外部写操作的本地跟踪（与支付 Mock 对账对齐）
TOOL_OP_TRANSITIONS: dict[ToolOpStatus, frozenset[ToolOpStatus]] = {
    ToolOpStatus.PENDING: frozenset(
        {ToolOpStatus.CONFIRMED, ToolOpStatus.FAILED, ToolOpStatus.UNKNOWN}
    ),
    ToolOpStatus.UNKNOWN: frozenset(
        {ToolOpStatus.CONFIRMED, ToolOpStatus.FAILED, ToolOpStatus.PENDING}
    ),
    ToolOpStatus.CONFIRMED: frozenset(),
    ToolOpStatus.FAILED: frozenset(),
}


def assert_task_transition(from_s: TaskStatus, to_s: TaskStatus) -> None:
    if to_s not in TASK_TRANSITIONS.get(from_s, frozenset()):
        raise ValueError(f"illegal task transition {from_s.value} -> {to_s.value}")


def assert_workflow_transition(from_s: WorkflowStatus, to_s: WorkflowStatus) -> None:
    if to_s not in WORKFLOW_TRANSITIONS.get(from_s, frozenset()):
        raise ValueError(
            f"illegal workflow transition {from_s.value} -> {to_s.value}"
        )


def assert_tool_op_transition(from_s: ToolOpStatus, to_s: ToolOpStatus) -> None:
    if to_s not in TOOL_OP_TRANSITIONS.get(from_s, frozenset()):
        raise ValueError(
            f"illegal tool_operation transition {from_s.value} -> {to_s.value}"
        )