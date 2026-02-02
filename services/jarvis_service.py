from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from services.review_brain import ReviewBrain
from core.explain_engine import explain_results
from llmexplainer.llm_wrapper import explain_with_llm
from core.sarif_exporter import to_sarif
from fastapi.responses import JSONResponse


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



# Health

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "jarvis-sandbox"
    }


# G.1 — Unified DevSync Review Endpoint
@app.post("/review")
def review(req: ReviewRequest):
    """
    Single-call, DevSync-ready review endpoint.
    Includes:
    - Deterministic analysis
    - Deterministic explanations
    - Deterministic auto-fixes (G.2)
    - Scope grouping (G.3)
    - Optional LLM presentation (F.x)
    """

    # 1) Deterministic analysis
    raw_issues = brain.review_code(req.dict())

    # 2) Deterministic explanation layer
    explained_issues = explain_results(raw_issues)

    # 3) Summary block
    summary = {
        "issue_count": len(explained_issues),
        "error_count": sum(1 for i in explained_issues if i["severity"] == "error"),
        "warning_count": sum(1 for i in explained_issues if i["severity"] == "warning"),
        "highest_severity": (
            "error"
            if any(i["severity"] == "error" for i in explained_issues)
            else "warning" if explained_issues else "none"
        ),
    }

    # 4) Optional LLM presentation layer (non-blocking)
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

    # 5) Final unified response
    return {
        "success": True,
        "summary": summary,
        "issues": explained_issues,
        "llm_explanation": llm_block,
        "metadata": {
            "schema_version": "1.0",
            "engine_version": "sandbox-1.0",
            "analysis_scope": "single-file",
            "llm_used": llm_block["present"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }



# G.4 — CI / SARIF Export Endpoint

@app.post("/review/sarif")
def review_sarif(req: ReviewRequest):
    """
    CI / GitHub Code Scanning compatible SARIF export.
    Deterministic only.
    No LLM involvement.
    """

    raw_issues = brain.review_code(req.dict())
    explained = explain_results(raw_issues)

    sarif = to_sarif(
        issues=explained,
        file_path=req.file or "unknown"
    )

    return JSONResponse(content=sarif)
