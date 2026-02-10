import json
from pathlib import Path
from datetime import datetime

USAGE_DIR = Path("usage")
USAGE_DIR.mkdir(exist_ok=True)


def _get_usage_file(org: str) -> Path:
    return USAGE_DIR / f"{org}.json"


def track_usage(org: str | None):
    """
    H5 — Simple per-org usage tracking
    JSON file per org.
    """

    if not org:
        return  # no org → skip tracking

    usage_file = _get_usage_file(org)

    if usage_file.exists():
        try:
            data = json.loads(usage_file.read_text())
        except Exception:
            data = {}
    else:
        data = {}

    data.setdefault("org", org)
    data.setdefault("total_scans", 0)

    data["total_scans"] += 1
    data["last_scan"] = datetime.utcnow().isoformat() + "Z"

    with open(usage_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print("[USAGE]", data)