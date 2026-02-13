# wisdomai/services/routes/chat.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import os
import requests

router = APIRouter()

# ================================
# ENV
# ================================
GROQ_KEY = os.getenv("LLM_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

# ================================
# SESSION MEMORY (in-RAM)
# ================================
CHAT_MEMORY: dict[str, list] = {}

# ================================
# Request schema
# ================================
class ChatRequest(BaseModel):
    message: str
    session_id: str
    code: Optional[str] = ""
    file: Optional[str] = ""
    language: Optional[str] = "python"

# ================================
# Helper — build system prompt
# ================================
def build_system_prompt(code: str, file: str, language: str) -> str:
    return f"""
You are WISDOM AI — a senior software engineer and coding partner.

Speak like a helpful senior developer friend.
Casual but highly intelligent.
Clear explanations.
Give full code when needed.

Current file: {file}
Language: {language}

User code context:
{code[:4000] if code else "No code provided"}
"""

# ================================
# Main chat endpoint
# ================================
@router.post("/api/wisdom/chat")
def wisdom_chat(req: ChatRequest):

    if not GROQ_KEY:
        return {
            "success": False,
            "reply": "LLM key missing on server."
        }

    # -------------------------------
    # get session history
    # -------------------------------
    history = CHAT_MEMORY.get(req.session_id, [])

    # -------------------------------
    # build messages
    # -------------------------------
    messages = [
        {
            "role": "system",
            "content": build_system_prompt(req.code, req.file, req.language)
        }
    ]

    # previous messages
    for m in history[-8:]:
        messages.append(m)

    # new user message
    messages.append({
        "role": "user",
        "content": req.message
    })

    # -------------------------------
    # call GROQ
    # -------------------------------
    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.5
            },
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        reply = data["choices"][0]["message"]["content"]

    except Exception as e:
        return {
            "success": False,
            "reply": "Wisdom chat temporarily unavailable."
        }

    # -------------------------------
    # save memory
    # -------------------------------
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})
    CHAT_MEMORY[req.session_id] = history[-20:]

    return {
        "success": True,
        "reply": reply
    }