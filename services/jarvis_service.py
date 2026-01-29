# jarvistools/services/jarvis_service.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from services.review_brain import ReviewBrain



app = FastAPI(title="Jarvis Code Review Service")

# =========================
# Init brain
# =========================

brain = ReviewBrain()

# =========================
# Schemas
# =========================

class ReviewRequest(BaseModel):
    file: str
    language: str
    code: str
    scope: str
    range: Optional[dict] = None


class ReviewItem(BaseModel):
    severity: str
    category: str
    message: str
    confidence: str


class ReviewResponse(BaseModel):
    success: bool
    results: List[ReviewItem]


# =========================
# Routes
# =========================

@app.get("/health")
def health():
    return {"status": "ok", "service": "jarvis"}


@app.post("/review_code", response_model=ReviewResponse)
def review_code(req: ReviewRequest):
    results = brain.review_code(req.dict())

    return {
        "success": True,
        "results": results,
    }
