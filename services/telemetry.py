# services/telemetry.py
import json
from pathlib import Path
from datetime import datetime
import uuid

LOG_DIR = Path("logs")
AUDIT_LOG = LOG_DIR / "audit.log"

# ensure log folder exists safely
try:
    LOG_DIR.mkdir(exist_ok=True)
except Exception as e:
    print("[AUDIT INIT ERROR]", e)


def _write_log(entry: dict):
    try:
        print("[AUDIT]", json.dumps(entry))
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print("[AUDIT WRITE ERROR]", e)


def log_review_event(
    *,
    org: str | None,
    file: str,
    language: str,
    issue_count: int,
    error_count: int,
    warning_count: int,
    policy_status: str,
    policy_version: str,
    profile: str,
    processing_ms: int,
    signature_valid: bool = True,
):
    """
    H4 — Enterprise audit logging
    Writes structured JSONL logs.
    One line per review request.
    """

    entry = {
        "event": "review_completed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": str(uuid.uuid4()),
        "org": org,
        "file": file,
        "language": language,
        "summary": {
            "issues": issue_count,
            "errors": error_count,
            "warnings": warning_count,
        },
        "policy": {
            "status": policy_status,
            "version": policy_version,
            "profile": profile,
        },
        "security": {
            "signature_valid": signature_valid
        },
        "performance": {
            "processing_ms": processing_ms
        }
    }

    _write_log(entry)