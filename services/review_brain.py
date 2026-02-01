# services/review_brain.py

from typing import List, Dict

from core.ast_analyzer import analyze_python_ast
from core.structure_analyzer import analyze_structure
from core.complexity_engine import analyze_complexity
from core.cfg_engine import analyze_cfg
from core.dfg_engine import analyze_dfg
from core.taint_engine import analyze_taint
from core.architecture_engine import analyze_architecture


# -----------------------------------
# Regex prefilter (ONLY destructive literals)
# -----------------------------------

DANGEROUS_PATTERNS = [
    ("rm -rf", "This command deletes files recursively and is extremely dangerous."),
    ("format c:", "This command formats a disk and destroys data."),
    ("mkfs", "This command formats a filesystem and can destroy data."),
]


class ReviewBrain:
    def __init__(self):
        print("[ReviewBrain] Initialized (analysis-only mode)")

    def review_code(self, payload: dict) -> List[Dict]:
        code = payload.get("code", "")
        language = payload.get("language", "unknown")

        results: List[Dict] = []

        # -----------------------------------
        # 1) Regex Prefilter (non-AST only)
        # -----------------------------------
        lowered = code.lower()
        for pattern, message in DANGEROUS_PATTERNS:
            if pattern in lowered:
                results.append({
                    "rule_id": "REGEX_DESTRUCTIVE_COMMAND",
                    "severity": "error",
                    "category": "security",
                    "message": message,
                    "confidence": "high",
                })

        # -----------------------------------
        # 2) AST Analyzer (security + bugs)
        # -----------------------------------
        if language.lower() in ["python", "py", "auto"]:
            results.extend(analyze_python_ast(code))

            # -----------------------------------
            # 3) Structure Analyzer (nesting, size)
            # -----------------------------------
            results.extend(analyze_structure(code))

            # -----------------------------------
            # 4) Complexity Engine (cyclomatic, params)
            # -----------------------------------
            results.extend(analyze_complexity(code))

            # -----------------------------------
            # 5) CFG Engine (Phase C.1)
            # -----------------------------------
            results.extend(analyze_cfg(code))

            # -----------------------------------
            # 5.5) DFG Engine (Phase C.2)
            # -----------------------------------
            results.extend(analyze_dfg(code))

            # -----------------------------------
            # 7) Taint Engine (Phase C.3)
            # -----------------------------------
            results.extend(analyze_taint(code))

            # -----------------------------------
            # 8) Architecture Engine (Phase D.1)
            # -----------------------------------
            results.extend(analyze_architecture(code))




        # -----------------------------------
        #  Clean Code Fallback
        # -----------------------------------
        if not results:
            results.append({
                "rule_id": "CLEAN_CODE",
                "severity": "info",
                "category": "style",
                "message": "No critical issues detected by static analyzers.",
                "confidence": "low",
            })

        return results
       
