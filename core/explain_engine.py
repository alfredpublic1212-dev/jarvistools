# core/explain_engine.py

from typing import Dict, List


# ------------------------------------------------------------------
# Canonical explanation registry (DETERMINISTIC, VERSIONABLE)
# ------------------------------------------------------------------

RULE_EXPLANATIONS: Dict[str, Dict[str, str]] = {

    # ---------------- CFG ----------------
    "CFG_DEAD_AFTER_RETURN": {
        "summary": "Unreachable code after return.",
        "detail": "Any statements after a return statement will never execute.",
        "remediation": "Remove unreachable code or move logic before the return."
    },

    "CFG_INFINITE_LOOP_CONFIRMED": {
        "summary": "Confirmed infinite loop.",
        "detail": "The loop has no break, return, or exit path.",
        "remediation": "Add a terminating condition or an explicit break."
    },

    # ---------------- DFG ----------------
    "DFG_USE_BEFORE_ASSIGN": {
        "summary": "Variable used before assignment.",
        "detail": "The variable is read before any value is assigned to it.",
        "remediation": "Assign a value before using the variable."
    },

    "DFG_UNUSED_VARIABLE": {
        "summary": "Unused variable.",
        "detail": "The variable is assigned but never read.",
        "remediation": "Remove the variable or use it meaningfully."
    },

    # ---------------- TAINT ----------------
    "TAINT_SINK_REACHED": {
        "summary": "Tainted data reached a dangerous sink.",
        "detail": "Untrusted input flows into a sensitive operation.",
        "remediation": "Validate, sanitize, or block untrusted input."
    },

    # ---------------- RESOURCE ----------------
    "RESOURCE_FILE_NOT_CLOSED": {
        "summary": "File opened but never closed.",
        "detail": "The file resource is not released, which can cause leaks.",
        "remediation": "Use a 'with open(...)' block or call close()."
    },

    # ---------------- ARCHITECTURE ----------------
    "ARCH_UNUSED_IMPORT": {
        "summary": "Unused import.",
        "detail": "The imported module is never referenced.",
        "remediation": "Remove unused imports to reduce clutter."
    },

    "ARCH_MIXED_CONCERNS": {
        "summary": "Mixed concerns detected.",
        "detail": "The module combines IO/system logic with business logic.",
        "remediation": "Separate IO handling and core logic into different modules."
    },

    "ARCH_GOD_MODULE": {
        "summary": "God module detected.",
        "detail": "The module has too many responsibilities.",
        "remediation": "Split the module into smaller, focused modules."
    },
}


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def explain_results(results: List[Dict]) -> List[Dict]:
    """
    Attach explanations to analyzer results.
    Deterministic mapping only.
    """

    explained: List[Dict] = []

    for r in results:
        rule_id = r.get("rule_id")
        explanation = RULE_EXPLANATIONS.get(rule_id)

        if explanation:
            explained.append({
                **r,
                "explanation": explanation
            })
        else:
            explained.append(r)

    return explained
