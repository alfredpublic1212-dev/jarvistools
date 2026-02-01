# llmexplainer/llm_guard.py
FORBIDDEN_PHRASES = [
    "new issue",
    "additional problem",
    "another vulnerability",
    "i found",
    "this code",
    "you should also check",
]

def guard_llm_output(text: str) -> str:
    lowered = text.lower()

    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            raise ValueError("LLM output violated sandbox constraints.")

    return text
