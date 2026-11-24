"""领域模型：Workflow / Task / ToolOperation 枚举与 business_key（图 04–05）。

- Workflow：整单生命周期（含 NEEDS_REVIEW、补偿窗口）
- Task：可租约、可恢复的步骤（refund / coupon DAG）
- ToolOperation：对外部支付写的幂等记录（与 business_key 1:1）
"""
from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Any


class WorkflowStatus(str, enum.Enum):
    """工作流级状态；NEEDS_REVIEW 时 Gateway 拒绝新写（图 08）。"""

    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    COMPENSATING = "COMPENSATING"
    COMPENSATED = "COMPENSATED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class TaskStatus(str, enum.Enum):
    """步骤状态；UNKNOWN 表示远端结果不确定，须查询而非盲 POST（图 02/05）。"""

    WAITING = "WAITING"
    READY = "READY"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ToolOpStatus(str, enum.Enum):
    """对外部 tool（支付退款等）的本地镜像状态。"""

    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


BUSINESS_KEY_PATTERN = re.compile(
    r"^[^:]+:(refund\.create|coupon\.issue):[^:]+:[^:]+$"
)


def make_business_key(
    tenant: str, tool: str, order_id: str, after_sale_id: str
) -> str:
    """Slide 04: stable id for external writes (not task_id)."""
    return f"{tenant}:{tool}:{order_id}:{after_sale_id}"


@dataclass(frozen=True)
class BusinessKeyParts:
    tenant: str
    tool: str
    order_id: str
    after_sale_id: str


def parse_business_key(key: str) -> BusinessKeyParts:
    parts = key.split(":", 3)
    if len(parts) != 4:
        raise ValueError(f"invalid business_key: {key}")
    return BusinessKeyParts(*parts)