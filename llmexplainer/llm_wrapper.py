import os
import requests
from .prompt_contract import build_prompt

API_KEY = os.getenv("LLM_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

def explain_with_llm(findings: list[dict]) -> str:
    # Hard fail early if key missing (prevents silent crashes)
    if not API_KEY:
        return "LLM API key is not configured."

    prompt = build_prompt(findings)

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            # SAFE MODEL WORKS ON FREE GROQ
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional AI code review explainer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.4,
        },
        timeout=30,
    )

    # If Groq itself errors (403 / 429 / 5xx)
    try:
        response.raise_for_status()
    except requests.HTTPError:
        return "The AI explainer is temporarily unavailable."

    data = response.json()

    # ABSOLUTE SAFETY GUARD (NO MORE 500s)
    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        return "The AI explainer could not generate a response."

    message = choices[0].get("message", {})
    return message.get("content", "").strip()
