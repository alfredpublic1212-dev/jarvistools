# services/review_brain.py

from typing import List, Dict
from core.ast_analyzer import analyze_python_ast
from core.structure_analyzer import analyze_structure
from core.complexity_engine import analyze_complexity


DANGEROUS_PATTERNS = [
    ("rm -rf", "This command deletes files recursively and is extremely dangerous."),
    ("mkfs", "This command formats a filesystem and destroys data."),
]


class ReviewBrain:
    def review_code(self, payload: dict) -> List[Dict]:
        code = payload.get("code", "")
        language = payload.get("language", "unknown").lower()

        results: List[Dict] = []

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

        if language in ("python", "py", "auto"):
            results.extend(analyze_python_ast(code))
            results.extend(analyze_structure(code))
            results.extend(analyze_complexity(code))

        if not results:
            results.append({
                "rule_id": "CLEAN_CODE",
                "severity": "info",
                "category": "style",
                "message": "No critical issues detected by static analyzers.",
                "confidence": "low",
            })

        return results
