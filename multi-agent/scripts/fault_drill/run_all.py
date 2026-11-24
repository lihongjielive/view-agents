#!/usr/bin/env python3
"""Run slide-11 fault drills outside pytest."""
from __future__ import annotations

import sys

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


def main() -> int:
    failed = 0
    for name, fn in DRILLS:
        try:
            fn()
            print(f"[OK] {name}")
        except Exception as exc:
            failed += 1
            print(f"[FAIL] {name}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())