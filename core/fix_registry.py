from typing import Dict, Optional


def fix_use_before_assign(issue: Dict, full_code: str) -> Optional[Dict]:
    """
    Deterministic fix for DFG_USE_BEFORE_ASSIGN.
    Strategy: move assignment before first usage.
    SAFE: single-variable, same scope only.
    """

    var_name = issue["message"].split("'")[1]

    lines = full_code.splitlines()

    assign_line = None
    use_line = issue["location"]["line"] - 1

    for i, line in enumerate(lines):
        if line.strip().startswith(f"{var_name} ="):
            assign_line = i
            break

    if assign_line is None or assign_line > use_line:
        return None

    new_lines = lines[:]
    assign_stmt = new_lines.pop(assign_line)
    new_lines.insert(use_line, assign_stmt)

    return {
        "available": True,
        "type": "reorder",
        "description": f"Move assignment of '{var_name}' before its usage.",
        "patch": {
            "before": "\n".join(lines),
            "after": "\n".join(new_lines),
        },
    }


FIX_HANDLERS = {
    "DFG_USE_BEFORE_ASSIGN": fix_use_before_assign,
}
