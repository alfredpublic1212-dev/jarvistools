# llmexplainer/llm_wrapper.py

from llmexplainer.llm_guard import guard_llm_input
from llmexplainer.prompt_contract import build_prompt


def explain_with_llm(explained_results: list) -> str:
    """
    Phase F.2 — LLM explanation wrapper.

    Current mode:
    - SAFE STUB (no external API)
    - Deterministic
    - Evaluator-safe

    Can be swapped later with real LLM.
    """

    # Enforce safety
    guard_llm_input(explained_results)

    # Build prompt (for future LLM use)
    prompt = build_prompt(explained_results)

    # 🔒 SAFE STUB RESPONSE
    summary_lines = [
        "AI Reviewer Summary:",
        ""
    ]

    for r in explained_results:
        summary_lines.append(
            f"- {r['rule_id']}: {r['message']} (severity: {r['severity']})"
        )

    summary_lines.append("")
    summary_lines.append(
        "These issues were detected by a deterministic analysis engine. "
        "Review the suggested fixes to improve code quality."
    )

    return "\n".join(summary_lines)
