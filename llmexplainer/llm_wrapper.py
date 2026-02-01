# llmexplainer/llm_wrapper.py
import os
import requests
from .prompt_contract import build_prompt

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("LLM_MODEL", "llama3")

def explain_with_llm(findings: list[dict]) -> str:
    prompt = build_prompt(findings)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    return data.get("response", "").strip()
