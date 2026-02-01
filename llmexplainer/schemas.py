# llmexplainer/schemas.py
from pydantic import BaseModel
from typing import List, Dict


class ReviewItem(BaseModel):
    rule_id: str
    severity: str
    category: str
    message: str
    confidence: str
    explanation: Dict | None = None
    trace: Dict | None = None
    remediation_playbook: Dict | None = None


class ExplainLLMRequest(BaseModel):
    results: List[ReviewItem]


class ExplainLLMResponse(BaseModel):
    success: bool
    results: List[Dict]
