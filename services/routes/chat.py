# services/routes/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os, json, requests

from wisdom_brain.intent_engine import detect_intent
from wisdom_brain.context_builder import build_context
from wisdom_brain.system_prompt import SYSTEM_PROMPT
from services.project_memory import init_db, save_message, load_memory

router = APIRouter()
init_db()
GROQ_KEY = os.getenv("LLM_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"


class ChatRequest(BaseModel):
    message: str
    session_id: str
    code: Optional[str] = ""
    file: Optional[str] = ""
    language: Optional[str] = "python"

@router.post("/api/wisdom/chat")
async def wisdom_chat(req: ChatRequest):

    if not GROQ_KEY:
        return {"success": False, "reply": "LLM key missing."}

    project_id = req.session_id
    history = load_memory(project_id)

    # 🧠 INTENT
    intent = detect_intent(req.message)

    # 🧠 CONTEXT
    context = build_context(
        message=req.message,
        intent=intent,
        code=req.code or "",
        file=req.file or "",
        language=req.language or "python",
        history=history
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context},
    ]

    for m in history[-8:]:
        messages.append(m)

    messages.append({"role": "user", "content": req.message})

    def stream():
        try:
            with requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.6,
                    "stream": True
                },
                stream=True,
                timeout=120
            ) as r:

                full_reply = ""

                for line in r.iter_lines():
                    if not line:
                        continue

                    decoded = line.decode("utf-8")

                    if decoded.startswith("data: "):
                        data = decoded.replace("data: ", "")

                        if data == "[DONE]":
                            break

                        try:
                            json_data = json.loads(data)
                            token = json_data["choices"][0]["delta"].get("content", "")

                            if token:
                                full_reply += token
                                yield token

                        except:
                            continue

                # save memory after stream finishes
                save_message(project_id, "user", req.message)
                save_message(project_id, "assistant", full_reply)

        except Exception as e:
            yield "\n[Wisdom stream error]"

    return StreamingResponse(stream(), media_type="text/plain")