import json
from pathlib import Path


ORG_POLICY_DIR = Path(__file__).parent / "org_policies"


def load_org_policy(org_name: str) -> dict:
    """
    Loads organization-specific policy config.
    """

    if not org_name:
        return {}

    policy_file = ORG_POLICY_DIR / f"{org_name}.json"

    if not policy_file.exists():
        return {}

    try:
        with open(policy_file, "r") as f:
            return json.load(f)
    except Exception:
        return {}