# core/org_policy_loader.py
import json
from pathlib import Path
from core.security.verify_policy import verify_policy_signature


# Folder where all org policies live
POLICY_DIR = Path("core/org_policies")


def load_org_policy(org: str) -> dict:
    """
    H3 — Enterprise Organization Policy Loader

    Loads organization-specific policy config ONLY if:
    - policy exists
    - signature exists
    - signature is valid

    This prevents:
    - tampered policies
    - fake configs
    - CI bypass attacks

    Used by:
    - DevSync
    - CI pipelines
    - Enterprise customers
    """

    # No org provided → return empty (use default runtime policy)
    if not org:
        return {}

    policy_file = POLICY_DIR / f"{org}.json"

    # If org policy missing → hard fail (enterprise safety)
    if not policy_file.exists():
        raise Exception(f"[POLICY] Org policy not found: {org}")

    #VERIFY SIGNATURE BEFORE LOADING
    # This ensures policy was signed by YOU (Jarvis owner)
    verify_policy_signature(org)

    # Load verified policy
    with open(policy_file, "r") as f:
        return json.load(f)