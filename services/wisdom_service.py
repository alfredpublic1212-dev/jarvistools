# services/wisdom_service.py
import time
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from fastapi.responses import JSONResponse

from services.rate_limiter import enforce_rate_limit
from core.security.api_auth import authenticate_request
from services.review_brain import ReviewBrain
from core.explain_engine import explain_results
from core.policy_engine import evaluate_policy
from llmexplainer.llm_wrapper import explain_with_llm
from core.sarif_exporter import to_sarif
from core.org_policy_loader import load_org_policy
from services.telemetry import log_review_event
from services.usage_tracker import track_usage
from services.routes.chat import router as chat_router

# =========================
# App init
# =========================
app = FastAPI(title="WISDOM AI Code Intelligence Engine")
brain = ReviewBrain()
app.include_router(chat_router)

# =========================
# Request Schema
# =========================
class ReviewRequest(BaseModel):
    file: str
    language: str
    code: str
    scope: str = "file"
    range: Optional[dict] = None
    policy: Optional[dict] = None


# =========================
# Health
# =========================
@app.get("/health")
def health():
    return {"status": "ok", "service": "wisdom-ai"}


# =========================
# Schema discovery
# =========================
@app.get("/review/schema")
def review_schema():
    return ReviewRequest.model_json_schema()


# =========================
# MAIN REVIEW ENDPOINT
# =========================
@app.post("/review")
def review(
    req: ReviewRequest,
    org_from_key: str = Depends(authenticate_request)  # H6 AUTH
):
    start_time = time.time()

    # org from API key (secure source of truth)
    org_name = org_from_key

    # =========================
    # H7 RATE LIMIT CHECK (DO FIRST)
    # =========================
    enforce_rate_limit(org_name)

    # =========================
    # 1 Deterministic analysis
    # =========================
    raw_issues = brain.review_code(req.dict())

    # =========================
    # 2 Deterministic explanation
    # =========================
    explained_issues = explain_results(raw_issues)

    # =========================
    # POLICY SYSTEM (H1–H3)
    # =========================
    policy_cfg = req.policy or {}

    policy_version = policy_cfg.get("version", "v1")
    profile = policy_cfg.get("profile", "balanced")
    warning_threshold = policy_cfg.get("warning_threshold", 5)

    # load org policy override
    if org_name:
        org_policy = load_org_policy(org_name)
        if org_policy:
            policy_version = org_policy.get("policy_version", policy_version)
            profile = org_policy.get("profile", profile)
            warning_threshold = org_policy.get("warning_threshold", warning_threshold)

    # evaluate policy
    policy_result = evaluate_policy(
        explained_issues,
        policy_version=policy_version,
        profile=profile,
        warning_threshold=warning_threshold
    )

    # =========================
    # Summary
    # =========================
    summary = {
        "issue_count": len(explained_issues),
        "error_count": policy_result.get("error_count", 0),
        "warning_count": policy_result.get("warning_count", 0),
        "highest_severity": (
            "error"
            if policy_result.get("error_count", 0) > 0
            else "warning" if policy_result.get("warning_count", 0) > 0
            else "none"
        ),
    }

    # =========================
    # Optional LLM explanation
    # =========================
    try:
        llm_text = explain_with_llm(explained_issues)
        llm_block = {"present": True, "content": llm_text}
    except Exception:
        llm_block = {"present": False, "content": None}

    # =========================
    # Response
    # =========================
    response = {
        "success": True,
        "summary": summary,
        "issues": explained_issues,
        "policy": policy_result,
        "llm_explanation": llm_block,
        "metadata": {
            "schema_version": "1.2",
            "engine_version": "wisdom-1.0",
            "analysis_scope": "single-file",
            "llm_used": llm_block["present"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }

    # =========================
    # H4 — AUDIT LOGGING
    # =========================
    try:
        processing_ms = int((time.time() - start_time) * 1000)

        log_review_event(
            org=org_name,
            file=req.file,
            language=req.language,
            issue_count=summary["issue_count"],
            error_count=summary["error_count"],
            warning_count=summary["warning_count"],
            policy_status=policy_result["status"],
            policy_version=policy_version,
            profile=profile,
            processing_ms=processing_ms,
            signature_valid=True
        )
    except Exception as e:
        print("[AUDIT LOG ERROR]", e)

    # =========================
    # H5 — USAGE TRACKING
    # =========================
    try:
        track_usage(org_name)
    except Exception as e:
        print("[USAGE TRACK ERROR]", e)

    # =========================
    # CI status semantics
    # =========================
    status_code = 200 if policy_result["status"] == "pass" else 422
    return JSONResponse(content=response, status_code=status_code)


# =========================
# SARIF EXPORT ENDPOINT
# =========================
@app.post("/review/sarif")
def review_sarif(
    req: ReviewRequest,
    org_from_key: str = Depends(authenticate_request)
):
    org_name = org_from_key

    # RATE LIMIT for SARIF too
    enforce_rate_limit(org_name)

    raw_issues = brain.review_code(req.dict())
    explained = explain_results(raw_issues)

    sarif = to_sarif(
        issues=explained,
        file_path=req.file or "unknown"
    )

    return JSONResponse(content=sarif)