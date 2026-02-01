# llmexplainer/prompt_contract.py
SYSTEM_PROMPT = """
You are a code review explanation assistant.

RULES (ABSOLUTE):
- You are NOT allowed to discover new issues.
- You are NOT allowed to analyze raw code.
- You MUST only explain the given findings.
- You MUST NOT contradict the findings.
- You MUST NOT introduce new risks or warnings.
- You MUST stay concise, technical, and factual.

You are an explanation layer, not an analyzer.
"""

def build_prompt(results: list[dict]) -> str:
    bullets = []

    for r in results:
        bullets.append(
            f"- Rule: {r['rule_id']}\n"
            f"  Severity: {r['severity']}\n"
            f"  Category: {r['category']}\n"
            f"  Message: {r['message']}\n"
            f"  Confidence: {r['confidence']}"
        )

    joined = "\n".join(bullets)

    return f"""
The following static analysis findings were produced by a deterministic engine.

Explain them clearly for a developer.

Findings:
{joined}

For each finding:
- Explain why it matters
- Suggest improvement
- Do NOT add new findings
"""
