# llmexplainer/prompt_contract.py

def build_prompt(explained_results: list) -> str:
    """
    Deterministic prompt contract.
    NO reasoning authority.
    NO decisions.
    Explanation-only.
    """

    lines = [
        "You are an AI code reviewer assistant.",
        "Explain the following verified findings in simple terms.",
        "Do NOT invent new issues.",
        "Do NOT suggest unsafe actions.",
        ""
    ]

    for idx, r in enumerate(explained_results, start=1):
        lines.append(f"Issue {idx}:")
        lines.append(f"- Type: {r['rule_id']}")
        lines.append(f"- Severity: {r['severity']}")
        lines.append(f"- Description: {r['message']}")

        explanation = r.get("explanation", {})
        if explanation:
            lines.append(f"- Why it matters: {explanation.get('detail')}")

        remediation = explanation.get("remediation") if explanation else None
        if remediation:
            lines.append(f"- How to fix: {remediation}")

        lines.append("")

    return "\n".join(lines)
