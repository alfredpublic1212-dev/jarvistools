# core/ast_analyzer.py

import ast
from typing import List, Dict


def _issue(severity: str, category: str, message: str, confidence: str = "high") -> Dict:
    return {
        "severity": severity,
        "category": category,
        "message": message,
        "confidence": confidence,
    }


def analyze_python_ast(code: str) -> List[Dict]:
    issues: List[Dict] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [
            _issue(
                "error",
                "syntax",
                f"Syntax error: {e.msg} (line {e.lineno})",
                "high",
            )
        ]

    for node in ast.walk(tree):

        # -----------------------------
        # 1. Infinite loop detection
        # while True:
        # -----------------------------
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                has_break = False
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Break):
                        has_break = True
                        break
                if not has_break:
                    issues.append(
                        _issue(
                            "warning",
                            "performance",
                            "Possible infinite loop detected: 'while True' without break.",
                            "high",
                        )
                    )

        # -----------------------------
        # 2. Bare except detection
        # except:
        # -----------------------------
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append(
                    _issue(
                        "warning",
                        "bug",
                        "Bare except detected. This will catch SystemExit, KeyboardInterrupt, etc.",
                        "high",
                    )
                )
            else:
                # except Exception as e: pass
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    issues.append(
                        _issue(
                            "warning",
                            "bug",
                            "Empty except block detected. Exception is silently ignored.",
                            "medium",
                        )
                    )

        # -----------------------------
        # 3. eval / exec via AST
        # -----------------------------
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "eval":
                    issues.append(
                        _issue(
                            "error",
                            "security",
                            "Use of eval() detected via AST. This allows arbitrary code execution.",
                            "high",
                        )
                    )
                if node.func.id == "exec":
                    issues.append(
                        _issue(
                            "error",
                            "security",
                            "Use of exec() detected via AST. This allows arbitrary code execution.",
                            "high",
                        )
                    )

        # -----------------------------
        # 4. os.system via AST
        # -----------------------------
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "os"
                    and node.func.attr == "system"
                ):
                    issues.append(
                        _issue(
                            "error",
                            "security",
                            "Use of os.system() detected via AST. This executes shell commands.",
                            "high",
                        )
                    )

    return issues
