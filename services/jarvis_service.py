from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from services.review_brain import ReviewBrain
from core.explain_engine import explain_results
from llmexplainer.llm_wrapper import explain_with_llm

# ============================================================
# App init
# ============================================================

app = FastAPI(title="Jarvis Sandbox Reasoning Service")
brain = ReviewBrain()

# ============================================================
# Schemas (internal + platform)
# ============================================================

class ReviewRequest(BaseModel):
    file: str
    language: str
    code: str
    scope: str
    range: Optional[dict] = None


class ReviewItem(BaseModel):
    rule_id: str
    severity: str
    category: str
    message: str
    confidence: str
    location: Optional[dict] = None
    code_snippet: Optional[str] = None
    explanation: Optional[dict] = None


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "jarvis-sandbox"
    }

# ============================================================
# 🔹 LEGACY / INTERNAL ENDPOINTS (KEPT)
# ============================================================

@app.post("/review_code")
def review_code(req: ReviewRequest):
    """
    Deterministic-only analysis.
    Internal / debugging / evaluator-safe.
    """
    results = brain.review_code(req.dict())
    return {
        "success": True,
        "results": results
    }


@app.post("/explain")
def explain(req: List[ReviewItem]):
    """
    Deterministic explanation layer.
    Internal use.
    """
    explained = explain_results([r.model_dump() for r in req])
    return {
        "success": True,
        "results": explained
    }


@app.post("/explain_llm")
def explain_llm(req: List[ReviewItem]):
    """
    LLM presentation layer only.
    Internal use.
    """
    explained = explain_results([r.model_dump() for r in req])
    llm_text = explain_with_llm(explained)

    return {
        "success": True,
        "llm_response": llm_text
    }

# ============================================================
# ✅ G.1 — PLATFORM / DEVSYNC ENDPOINT (OFFICIAL)
# ============================================================

@app.post("/review")
def review(req: ReviewRequest):
    """
    Single-call, DevSync-ready review endpoint.
    This is the ONLY endpoint platforms should use.
    """

    # 1. Deterministic analysis
    raw_issues = brain.review_code(req.dict())

    # 2. Deterministic explanation
    explained_issues = explain_results(raw_issues)

    # 3. Summary block
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

    # 4. Optional LLM presentation layer
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

    # 5. Final unified response
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
