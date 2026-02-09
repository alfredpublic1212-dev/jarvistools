# core/policy_engine.py
from typing import List, Dict, Optional


# ============================================================
# H.1 — VERSIONED POLICY ENGINE (ENTERPRISE FOUNDATION)
# ============================================================
# Goals:
# - Deterministic
# - Versioned policies
# - Backward compatible with G.5
# - Company-ready
# - CI-safe
# ============================================================


DEFAULT_POLICY_VERSION = "v1"


def evaluate_policy(
    issues: List[Dict],
    *,
    warning_threshold: int = 5,
    policy_version: Optional[str] = None,
) -> Dict:
    """
    H.1 — Versioned Policy Evaluation

    Default policy (v1):
    - Any error => FAIL
    - warnings > threshold => FAIL
    - else PASS

    Backward compatible with G.5.
    """

    version = policy_version or DEFAULT_POLICY_VERSION

    # --------------------------------------------------------
    # Count severities
    # --------------------------------------------------------
    error_count = sum(1 for i in issues if i.get("severity") == "error")
    warning_count = sum(1 for i in issues if i.get("severity") == "warning")

    # --------------------------------------------------------
    # POLICY VERSION: v1 (Balanced)
    # --------------------------------------------------------
    if version == "v1":

        if error_count > 0:
            return _build_result(
                status="fail",
                reason="errors_present",
                version=version,
                error_count=error_count,
                warning_count=warning_count,
                threshold=warning_threshold,
            )

        if warning_count > warning_threshold:
            return _build_result(
                status="fail",
                reason="warning_threshold_exceeded",
                version=version,
                error_count=error_count,
                warning_count=warning_count,
                threshold=warning_threshold,
            )

        return _build_result(
            status="pass",
            reason="within_policy_limits",
            version=version,
            error_count=error_count,
            warning_count=warning_count,
            threshold=warning_threshold,
        )

    # --------------------------------------------------------
    # Unknown policy version (future-proofing)
    # --------------------------------------------------------
    return _build_result(
        status="pass",
        reason="unknown_policy_version_default_pass",
        version=version,
        error_count=error_count,
        warning_count=warning_count,
        threshold=warning_threshold,
    )


# ============================================================
# INTERNAL: result builder (consistent structure)
# ============================================================
def _build_result(
    *,
    status: str,
    reason: str,
    version: str,
    error_count: int,
    warning_count: int,
    threshold: int,
) -> Dict:
    return {
        "status": status,
        "reason": reason,
        "policy_version": version,
        "error_count": error_count,
        "warning_count": warning_count,
        "threshold": threshold,
    }