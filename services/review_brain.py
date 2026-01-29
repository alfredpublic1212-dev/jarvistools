# jarvistools/services/review_brain.py

from typing import List, Dict

# Import ONLY logic — no runtime, no jarvis.py
from core.judge import evaluate
from core.score_engine import score_action
from core.ast_analyzer import analyze_python_ast


# -----------------------------
# Simple static danger patterns
# -----------------------------

DANGEROUS_PATTERNS = [
    ("os.system", "Executing shell commands via os.system is dangerous."),
    ("subprocess", "Using subprocess to execute shell commands can be dangerous."),
    ("rm -rf", "This command deletes files recursively and is extremely dangerous."),
    ("eval(", "Using eval() allows arbitrary code execution."),
    ("exec(", "Using exec() allows arbitrary code execution."),
    ("pickle.loads", "Untrusted pickle.loads can lead to code execution."),
    ("__import__", "Dynamic imports can be abused."),
    ("open(", "Check file operations for path traversal or overwrites."),
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
        # 1️ Static pattern checks (FAST, SAFE)
        # -----------------------------------

        lowered = code.lower()

        for pattern, message in DANGEROUS_PATTERNS:
            if pattern.lower() in lowered:
                results.append({
                    "severity": "error",
                    "category": "security",
                    "message": message,
                    "confidence": "high",
                })


        # -----------------------------------
        # 1.5 AST structural analysis (NEW)
        # -----------------------------------

        ast_issues = []
        if language.lower() in ["python", "py", "auto"]:
            ast_issues = analyze_python_ast(code)

        results.extend(ast_issues)


        # -----------------------------------
        # 2️ Ask Jarvis core to reason about it
        # -----------------------------------

        analysis_action = f"""
Analyze this code for:
- security issues
- dangerous behavior
- maintainability problems
- suspicious patterns

File: {file}
Language: {language}

Code:
{code}
""".strip()

        # Heuristic score
        score = score_action(analysis_action, context={})
        print("[ReviewBrain] ScoreEngine result: total =", score.total)

        # Policy judge
        decision = evaluate(
            analysis_action,
            context={},
            is_confirmed=True,  # always true: analysis-only mode
        )

        # If Jarvis judge is uncomfortable
        if not decision.allow:
            results.append({
                "severity": "warning",
                "category": "security",
                "message": decision.reason or "Jarvis core considers this code risky or unsafe.",
                "confidence": "medium",
            })

        # If long-horizon risk is high
        if score.total < -20:
            results.append({
                "severity": "warning",
                "category": "maintainability",
                "message": "Jarvis core predicts long-term structural or maintenance risk.",
                "confidence": "low",
            })

        # -----------------------------------
        # 3 If nothing found, return clean bill
        # -----------------------------------

        if not results:
            results.append({
                "severity": "info",
                "category": "style",
                "message": "No critical issues detected by Jarvis core or static analyzers.",
                "confidence": "low",
            })

        return results

