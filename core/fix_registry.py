# core/fix_registry.py
from typing import Dict, Optional


def fix_use_before_assign(issue: Dict, full_code: str) -> Optional[Dict]:
    """
    Deterministic fix for DFG_USE_BEFORE_ASSIGN.

    Strategy:
    - Insert a safe placeholder assignment BEFORE first usage
    - Does NOT guess value semantics
    - INLINE only (before / after snippets)

    Safety:
    - Single-variable
    - Same scope
    - No execution
    """

    location = issue.get("location")
    if not location:
        return None

    var_name = issue["message"].split("'")[1]
    lines = full_code.splitlines()

    use_line_idx = location["line"] - 1
    if use_line_idx < 0 or use_line_idx >= len(lines):
        return None

    before_snippet = lines[use_line_idx]

    # Preserve indentation
    indent = before_snippet[: len(before_snippet) - len(before_snippet.lstrip())]
    assignment_line = f"{indent}{var_name} = None"

    after_snippet = f"{assignment_line}\n{before_snippet}"

    return {
        "available": True,
        "type": "inline",
        "description": f"Initialize '{var_name}' before it is used.",
        "before": before_snippet,
        "after": after_snippet,
    }


FIX_HANDLERS = {
    "DFG_USE_BEFORE_ASSIGN": fix_use_before_assign,
}
