# wisdom_brain/intent_engine.py
def detect_intent(message: str) -> str:
    msg = message.lower()

    if "fix" in msg or "bug" in msg or "error" in msg:
        return "debug"

    if "optimize" in msg or "improve" in msg:
        return "optimize"

    if "architecture" in msg or "design" in msg:
        return "architecture"

    if "build" in msg or "create" in msg:
        return "generate"

    if "explain" in msg:
        return "explain"

    return "general"