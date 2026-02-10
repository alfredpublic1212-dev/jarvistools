# core/policy_engine.py
from typing import List, Dict

SUPPORTED_POLICY_VERSIONS = ["v1"]
SUPPORTED_PROFILES = ["balanced", "strict", "permissive"]


def evaluate_policy(
    issues: List[Dict],
    *,
    policy_version: str = "v1",
    profile: str = "balanced",
    warning_threshold: int = 5
) -> Dict:
    """
    H1 — Versioned + Profiled Policy Engine

    Supports:
    - versioned policies
    - strict / balanced / permissive profiles
    - configurable thresholds
    """

    # ------------------------------
    # Validate version
    # ------------------------------
    if policy_version not in SUPPORTED_POLICY_VERSIONS:
        return {
            "status": "fail",
            "reason": "unsupported_policy_version",
            "policy_version": policy_version,
        }

    if profile not in SUPPORTED_PROFILES:
        return {
            "status": "fail",
            "reason": "unsupported_policy_profile",
            "policy_version": policy_version,
            "profile": profile,
        }

    # ------------------------------
    # Count issues
    # ------------------------------
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")

    # ------------------------------
    # STRICT PROFILE
    # ------------------------------
    if profile == "strict":
        if error_count > 0 or warning_count > 0:
            return {
                "status": "fail",
                "reason": "strict_policy_violation",
                "policy_version": policy_version,
                "profile": profile,
                "error_count": error_count,
                "warning_count": warning_count,
            }

        return {
            "status": "pass",
            "reason": "strict_clean",
            "policy_version": policy_version,
            "profile": profile,
            "error_count": error_count,
            "warning_count": warning_count,
        }

    # ------------------------------
    # PERMISSIVE PROFILE
    # ------------------------------
    if profile == "permissive":
        if error_count > 0:
            return {
                "status": "fail",
                "reason": "errors_present",
                "policy_version": policy_version,
                "profile": profile,
                "error_count": error_count,
                "warning_count": warning_count,
            }

        return {
            "status": "pass",
            "reason": "permissive_pass",
            "policy_version": policy_version,
            "profile": profile,
            "error_count": error_count,
            "warning_count": warning_count,
        }

    # ------------------------------
    # BALANCED PROFILE (DEFAULT)
    # ------------------------------
    if error_count > 0:
        return {
            "status": "fail",
            "reason": "errors_present",
            "policy_version": policy_version,
            "profile": profile,
            "error_count": error_count,
            "warning_count": warning_count,
            "threshold": warning_threshold,
        }

    if warning_count > warning_threshold:
        return {
            "status": "fail",
            "reason": "warning_threshold_exceeded",
            "policy_version": policy_version,
            "profile": profile,
            "error_count": error_count,
            "warning_count": warning_count,
            "threshold": warning_threshold,
        }

    return {
        "status": "pass",
        "reason": "within_policy_limits",
        "policy_version": policy_version,
        "profile": profile,
        "error_count": error_count,
        "warning_count": warning_count,
        "threshold": warning_threshold,
    }