# llmexplainer/prompt_contract.py
SYSTEM_PROMPT = """
You are an AI code review explainer.

You are given VERIFIED findings produced by a deterministic static analysis engine.

RULES YOU MUST FOLLOW:
- Do NOT invent new issues
- Do NOT analyze code
- Do NOT reference source code directly
- Do NOT add opinions or judgments
- Do NOT suggest changes beyond the provided remediation
- Do NOT mention internal engines unless explicitly provided

YOUR JOB:
- Rewrite the findings into clear, professional, human-friendly review feedback
- Explain why each issue matters
- Suggest the provided remediation in natural language

Tone:
- Calm
- Professional
- Supportive
- Clear English
"""

def build_prompt(findings: list[dict]) -> str:
    lines = [SYSTEM_PROMPT, "\nThe following issues were detected:\n"]

    for i, f in enumerate(findings, 1):
        lines.append(
            f"""
Issue {i}:
Severity: {f.get("severity")}
Category: {f.get("category")}
Summary: {f.get("explanation", {}).get("summary")}
Details: {f.get("explanation", {}).get("detail")}
Suggested Fix: {f.get("explanation", {}).get("remediation")}
"""
        )

    lines.append(
        "\nWrite a natural-language code review explaining these findings to a developer."
    )

    return "\n".join(lines)
