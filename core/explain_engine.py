# core/explain_engine.py

from typing import Dict, List


# ------------------------------------------------------------------
# Canonical explanation + trace + remediation registry
# ------------------------------------------------------------------

RULE_METADATA: Dict[str, Dict[str, Dict]] = {

    # ================= DFG =================
    "DFG_USE_BEFORE_ASSIGN": {
        "explanation": {
            "summary": "Variable used before assignment.",
            "detail": "The variable is read before any value is assigned to it.",
            "remediation": "Assign a value before using the variable."
        },
        "trace": {
            "reasoning": "Variable load detected without prior assignment in scope.",
            "engine": "dfg_engine",
            "confidence_basis": "Scope-aware symbol tracking."
        },
        "playbook": {
            "goal": "Ensure variables are initialized before use.",
            "steps": [
                "Locate the first usage of the variable.",
                "Add an assignment before that usage.",
                "Ensure all code paths assign a value."
            ],
            "example_before": "print(x)",
            "example_after": "x = 0\nprint(x)"
        }
    },

    "DFG_UNUSED_VARIABLE": {
        "explanation": {
            "summary": "Unused variable.",
            "detail": "The variable is assigned but never read.",
            "remediation": "Remove the variable or use it meaningfully."
        },
        "trace": {
            "reasoning": "Assignment detected with no subsequent reads.",
            "engine": "dfg_engine",
            "confidence_basis": "Assignment/use mismatch."
        },
        "playbook": {
            "goal": "Reduce dead code and improve clarity.",
            "steps": [
                "Confirm the variable is not required.",
                "Remove the assignment if unnecessary.",
                "Or integrate the variable into logic."
            ],
            "example_before": "x = 5",
            "example_after": "# removed unused variable"
        }
    },

    # ================= RESOURCE =================
    "RESOURCE_FILE_NOT_CLOSED": {
        "explanation": {
            "summary": "File opened but never closed.",
            "detail": "The file resource is not released, which can cause leaks.",
            "remediation": "Use a context manager or explicitly close the file."
        },
        "trace": {
            "reasoning": "open() call detected without close() or with-statement.",
            "engine": "resource_engine",
            "confidence_basis": "Scope exit without release."
        },
        "playbook": {
            "goal": "Ensure file resources are always released.",
            "steps": [
                "Replace open() with a with-statement.",
                "Or call close() on all exit paths."
            ],
            "example_before": "f = open('a.txt')\ndata = f.read()",
            "example_after": "with open('a.txt') as f:\n    data = f.read()"
        }
    },

    # ================= ARCHITECTURE =================
    "ARCH_UNUSED_IMPORT": {
        "explanation": {
            "summary": "Unused import.",
            "detail": "The imported module is never referenced.",
            "remediation": "Remove unused imports."
        },
        "trace": {
            "reasoning": "Import detected with no symbol usage.",
            "engine": "architecture_engine",
            "confidence_basis": "Name usage analysis."
        },
        "playbook": {
            "goal": "Reduce clutter and improve maintainability.",
            "steps": [
                "Locate the unused import.",
                "Remove it from the import list.",
                "Re-run tests to ensure nothing breaks."
            ],
            "example_before": "import os",
            "example_after": "# import removed"
        }
    },

    "ARCH_GOD_MODULE": {
        "explanation": {
            "summary": "God module detected.",
            "detail": "The module handles too many responsibilities.",
            "remediation": "Split the module into smaller focused modules."
        },
        "trace": {
            "reasoning": "Multiple architectural thresholds exceeded.",
            "engine": "architecture_engine",
            "confidence_basis": "Aggregate structural heuristics."
        },
        "playbook": {
            "goal": "Improve modularity and separation of concerns.",
            "steps": [
                "Identify unrelated responsibilities.",
                "Group related functions/classes.",
                "Move them into separate modules."
            ],
            "example_before": "utils.py  # 2000 lines, mixed logic",
            "example_after": "io_utils.py\nmath_utils.py\ncore_logic.py"
        }
    }
}


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def explain_results(results: List[Dict]) -> List[Dict]:
    """
    Attach explanation, trace, and remediation playbooks.
    Deterministic. No execution. No guessing.
    """

    explained: List[Dict] = []

    for r in results:
        rule_id = r.get("rule_id")
        meta = RULE_METADATA.get(rule_id)

        enriched = dict(r)

        if meta:
            enriched["explanation"] = meta.get("explanation")
            enriched["trace"] = meta.get("trace")
            enriched["remediation_playbook"] = meta.get("playbook")

        if "location" in r:
            enriched["location"] = r["location"]

        explained.append(enriched)

    return explained
