import os
import requests
from .prompt_contract import build_prompt

API_KEY = os.getenv("LLM_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

def explain_with_llm(findings: list[dict]) -> str:
    prompt = build_prompt(findings)

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "You are a code review explainer."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
