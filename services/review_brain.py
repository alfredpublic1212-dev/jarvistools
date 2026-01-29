# jarvistools/services/review_brain.py

from typing import List, Dict

# Import ONLY static analysis logic
from core.ast_analyzer import analyze_python_ast


# -----------------------------
# Regex prefilter ONLY for things AST does NOT yet cover
# -----------------------------

DANGEROUS_PATTERNS = [
    ("rm -rf", "This command deletes files recursively and is extremely dangerous."),
    ("format c:", "This command formats a disk and destroys data."),
    ("mkfs", "This command formats a filesystem and can destroy data."),
]


class ReviewBrain:
    def __init__(self):
        print("[ReviewBrain] Initialized (analysis-only mode)")

    def review_code(self, payload: dict) -> List[Dict]:
        file = payload.get("file", "unknown")
        code = payload.get("code", "")
        language = payload.get("language", "unknown")

        print("[ReviewBrain] ================================")
        print("[ReviewBrain] Received review request")
        print("[ReviewBrain] File:", file)
        print("[ReviewBrain] Language:", language)
        print("[ReviewBrain] Code:\n", code)
        print("[ReviewBrain] ================================")

        results: List[Dict] = []

        # -----------------------------------
        # 1) Regex prefilter (ONLY for things AST does not cover)
        # -----------------------------------

        lowered = code.lower()
        for pattern, message in DANGEROUS_PATTERNS:
            if pattern in lowered:
                results.append({
                    "severity": "error",
                    "category": "security",
                    "message": message,
                    "confidence": "high",
                })

        # -----------------------------------
        # 2) AST structural analysis (PRIMARY)
        # -----------------------------------

        if language.lower() in ["python", "py", "auto"]:
            ast_issues = analyze_python_ast(code)
            results.extend(ast_issues)

        # -----------------------------------
        # 3) If nothing found, return clean bill
        # -----------------------------------

        if not results:
            results.append({
                "severity": "info",
                "category": "style",
                "message": "No critical issues detected by static analyzers.",
                "confidence": "low",
            })

        return results
