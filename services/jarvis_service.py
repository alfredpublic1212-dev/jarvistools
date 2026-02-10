import time
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from fastapi.responses import JSONResponse

from services.review_brain import ReviewBrain
from core.explain_engine import explain_results
from core.policy_engine import evaluate_policy
from llmexplainer.llm_wrapper import explain_with_llm
from core.sarif_exporter import to_sarif
from core.org_policy_loader import load_org_policy
from services.telemetry import log_review_event

# =========================
# App init
# =========================
app = FastAPI(title="Jarvis Sandbox Reasoning Service")
brain = ReviewBrain()


# =========================
# Request Schema (PUBLIC CONTRACT)
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
    return {
        "status": "ok",
        "service": "jarvis-sandbox"
    }


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
def review(req: ReviewRequest):

    start_time = time.time()

    # -------------------------
    # 1 Deterministic analysis
    # -------------------------
    raw_issues = brain.review_code(req.dict())

    # -------------------------
    # 2 Deterministic explanation
    # -------------------------
    explained_issues = explain_results(raw_issues)

    # =========================
    # H1 + H2 POLICY SYSTEM
    # =========================
    policy_cfg = req.policy or {}

    policy_version = policy_cfg.get("version", "v1")
    profile = policy_cfg.get("profile", "balanced")
    warning_threshold = policy_cfg.get("warning_threshold", 5)

    # H2 org override
    org_name = policy_cfg.get("org")
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
    # Optional LLM
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
            "engine_version": "sandbox-1.0",
            "analysis_scope": "single-file",
            "llm_used": llm_block["present"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }

    # =========================
    # H4 ENTERPRISE AUDIT LOGGING
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
    # CI status semantics
    # =========================
    status_code = 200 if policy_result["status"] == "pass" else 422
    return JSONResponse(content=response, status_code=status_code)


# =========================
# SARIF export endpoint
# =========================
@app.post("/review/sarif")
def review_sarif(req: ReviewRequest):

    raw_issues = brain.review_code(req.dict())
    explained = explain_results(raw_issues)

    sarif = to_sarif(
        issues=explained,
        file_path=req.file or "unknown"
    )

    return JSONResponse(content=sarif)