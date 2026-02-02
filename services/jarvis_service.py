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



# App init
app = FastAPI(title="Jarvis Sandbox Reasoning Service")
brain = ReviewBrain()



# Request schema
class ReviewRequest(BaseModel):
    file: str
    language: str
    code: str
    scope: str
    range: Optional[dict] = None

    # G.5 policy config (optional)
    policy: Optional[dict] = None


# Health

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "jarvis-sandbox"
    }



# G.1–G.6 — Unified Review Endpoint

@app.post("/review")
def review(req: ReviewRequest):
    """
    Single-call, DevSync + CI-ready review endpoint.

    Includes:
    - Deterministic analysis
    - Deterministic explanations
    - Auto-fixes (G.2)
    - Scope grouping (G.3)
    - Policy evaluation (G.5)
    - CI exit behavior (G.6)
    - Optional LLM presentation (F.x)
    """

    # 1) Deterministic analysis
    raw_issues = brain.review_code(req.dict())

    # 2) Deterministic explanation layer
    explained_issues = explain_results(raw_issues)

    # 3) Policy evaluation (G.5)
    policy_cfg = req.policy or {}
    warning_threshold = policy_cfg.get("warning_threshold", 5)

    policy_result = evaluate_policy(
        explained_issues,
        warning_threshold=warning_threshold
    )

    # 4) Summary block
    summary = {
        "issue_count": len(explained_issues),
        "error_count": policy_result["error_count"],
        "warning_count": policy_result["warning_count"],
        "highest_severity": (
            "error"
            if policy_result["error_count"] > 0
            else "warning" if policy_result["warning_count"] > 0
            else "none"
        ),
    }

    # 5) Optional LLM presentation (non-blocking)
    try:
        llm_text = explain_with_llm(explained_issues)
        llm_block = {
            "present": True,
            "content": llm_text
        }
    except Exception:
        llm_block = {
            "present": False,
            "content": None
        }

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

    # 6) G.6 — CI exit via HTTP status
    status_code = 200 if policy_result["status"] == "pass" else 422
    return JSONResponse(content=response, status_code=status_code)



# G.4 — SARIF Export (CI / GitHub Code Scanning)

@app.post("/review/sarif")
def review_sarif(req: ReviewRequest):
    """
    SARIF export for CI systems.
    Deterministic only.
    No policy gating.
    No LLM involvement.
    """

    raw_issues = brain.review_code(req.dict())
    explained = explain_results(raw_issues)

    sarif = to_sarif(
        issues=explained,
        file_path=req.file or "unknown"
    )

    return JSONResponse(content=sarif)
