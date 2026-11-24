"""Slide 11 fault-injection drills (callable from pytest)."""
from multi_agent.fault_drill.scenarios import (
    run_crash_before_offset,
    run_late_callback,
    run_lost_publish_ack,
    run_success_response_lost,
    run_worker_disconnect,
)

__all__ = [
    "run_lost_publish_ack",
    "run_crash_before_offset",
    "run_worker_disconnect",
    "run_success_response_lost",
    "run_late_callback",
]