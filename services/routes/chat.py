# wisdomai/services/routes/chat.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os
import requests

from wisdom_brain.intent_engine import detect_intent
from wisdom_brain.context_builder import build_context
from wisdom_brain.system_prompt import SYSTEM_PROMPT

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

    # =================================
    # 🧠 WISDOM BRAIN PIPELINE
    # =================================
    intent = detect_intent(req.message)

    context = build_context(
        message=req.message,
        intent=intent,
        code=req.code or "",
        file=req.file or "",
        language=req.language or "python",
        history=history
    )

    # -------------------------------
    # build messages for LLM
    # -------------------------------
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "system",
            "content": context
        }
    ]

    # previous chat memory
    for m in history[-8:]:
        messages.append(m)

    # new user message
    messages.append({
        "role": "user",
        "content": req.message
    })

    # -------------------------------
    # call GROQ LLM
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