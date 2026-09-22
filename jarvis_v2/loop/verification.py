"""Reusable verification helpers for action outcomes."""
from __future__ import annotations
from typing import Any
from .controller import Verification

def verify_action_success(actions, expected_success: int | None = None) -> Verification:
    failed=[a for a in actions if not a.success]
    if failed:
        return Verification(False, "Execution reported failure.", {"failed_tools": [a.tool for a in failed]})
    if expected_success is not None and len(actions) != expected_success:
        return Verification(False, "Execution count did not match expectation.", {"expected": expected_success, "actual": len(actions)})
    return Verification(True, "Execution completed successfully.", {"actions": len(actions)})
