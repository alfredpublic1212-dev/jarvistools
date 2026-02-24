#wisdom_brain/context_builder.py
def build_context(message, code=None, file=None, language=None, history=None, intent="general"):
    
    ctx = f"""
USER MESSAGE:
{message}

INTENT:
{intent}
"""

    if file:
        ctx += f"\nFILE: {file}"

    if language:
        ctx += f"\nLANGUAGE: {language}"

    if code:
        ctx += f"\nSELECTED CODE:\n{code}"

    if history:
        ctx += "\nPREVIOUS CHAT:\n"
        for h in history[-5:]:
            ctx += f"{h.get('role')}: {h.get('text')}\n"

    return ctx