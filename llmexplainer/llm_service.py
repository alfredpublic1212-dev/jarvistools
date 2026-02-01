# llmexplainer/llm_service.py
from fastapi import FastAPI, HTTPException
from llmexplainer.schemas import (
    ExplainLLMRequest,
    ExplainLLMResponse
)
from llmexplainer.prompt_contract import SYSTEM_PROMPT, build_prompt
from llmexplainer.llm_guard import guard_llm_output

app = FastAPI(title="Jarvis LLM Explainer")


# -----------------------------
# LLM CALL PLACEHOLDER
# -----------------------------
def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Replace this with:
    - Ollama
    - Self-hosted LLaMA
    - Fine-tuned model
    - ANYTHING later

    Sandbox is NOT affected.
    """
    # TEMP deterministic stub (safe for evaluation)
    return "These findings highlight maintainability and correctness issues. Addressing them will improve code quality."


# -----------------------------
# Routes
# -----------------------------
@app.post("/explain_llm", response_model=ExplainLLMResponse)
def explain_llm(req: ExplainLLMRequest):
    if not req.results:
        return {"success": True, "results": []}

    prompt = build_prompt([r.dict() for r in req.results])

    raw_output = call_llm(SYSTEM_PROMPT, prompt)

    try:
        safe_output = guard_llm_output(raw_output)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "results": [
            {
                "llm_summary": safe_output
            }
        ]
    }
