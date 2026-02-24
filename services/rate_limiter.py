# services/rate_limiter.py
import json
import os
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException


# CONFIG
USAGE_DIR = Path("usage")
LIMITS_FILE = Path("usage_limits.json")

# ensure usage folder exists
USAGE_DIR.mkdir(exist_ok=True)


def _today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def _load_limits():
    if not LIMITS_FILE.exists():
        return {}

    with open(LIMITS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_usage(org: str):
    usage_file = USAGE_DIR / f"{org}.json"

    if not usage_file.exists():
        return {
            "date": _today(),
            "count": 0
        }

    with open(usage_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_usage(org: str, data: dict):
    usage_file = USAGE_DIR / f"{org}.json"
    with open(usage_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)



# MAIN RATE LIMIT CHECK (H7)
def enforce_rate_limit(org: str):
    """
    H7 — Per-org daily rate limiter
    Blocks if daily scans exceeded
    """

    # DEV MODE BYPASS
    if os.getenv("DEV_MODE", "").lower() == "true":
        return

    limits = _load_limits()

    if org not in limits:
        # no limit configured → allow
        return

    daily_limit = limits[org].get("daily_limit", 100)

    usage = _load_usage(org)

    # reset if new day
    if usage["date"] != _today():
        usage = {
            "date": _today(),
            "count": 0
        }

    if usage["count"] >= daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily scan limit exceeded ({daily_limit}/day)."
        )

    # increment usage
    usage["count"] += 1
    _save_usage(org, usage)

    print(f"[RATE LIMIT] {org}: {usage['count']}/{daily_limit} today")