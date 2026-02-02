# core/policy_engine.py
from typing import List, Dict


def evaluate_policy(
    issues: List[Dict],
    *,
    warning_threshold: int = 5
) -> Dict:
    """
    G.5 — Policy Engine (Balanced)

    Rules:
    - Any error => FAIL
    - warnings > threshold => FAIL
    - else PASS
    """

    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")

    if error_count > 0:
        return {
            "status": "fail",
            "reason": "errors_present",
            "error_count": error_count,
            "warning_count": warning_count,
            "threshold": warning_threshold,
        }

    if warning_count > warning_threshold:
        return {
            "status": "fail",
            "reason": "warning_threshold_exceeded",
            "error_count": error_count,
            "warning_count": warning_count,
            "threshold": warning_threshold,
        }

    return {
        "status": "pass",
        "reason": "within_policy_limits",
        "error_count": error_count,
        "warning_count": warning_count,
        "threshold": warning_threshold,
    }
