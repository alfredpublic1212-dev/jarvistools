# core/ast_analyzer.py

import ast
from typing import List, Dict


def issue(rule_id: str, severity: str, category: str, message: str, confidence: str = "high") -> Dict:
    return {
        "rule_id": rule_id,
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
            issue(
                "SYNTAX_ERROR",
                "error",
                "syntax",
                f"Syntax error: {e.msg} (line {e.lineno})",
                "high",
            )
        ]

    for node in ast.walk(tree):

        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                if not any(isinstance(n, ast.Break) for n in ast.walk(node)):
                    issues.append(
                        issue(
                            "AST_INFINITE_LOOP",
                            "warning",
                            "performance",
                            "Possible infinite loop detected: 'while True' without break.",
                        )
                    )

        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append(
                    issue(
                        "AST_BARE_EXCEPT",
                        "warning",
                        "bug",
                        "Bare except detected. This catches SystemExit, KeyboardInterrupt, etc.",
                    )
                )
            elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                issues.append(
                    issue(
                        "AST_EMPTY_EXCEPT",
                        "warning",
                        "bug",
                        "Empty except block detected. Exception is silently ignored.",
                        "medium",
                    )
                )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "eval":
                issues.append(
                    issue(
                        "AST_SECURITY_EVAL",
                        "error",
                        "security",
                        "Use of eval() detected. This allows arbitrary code execution.",
                    )
                )
            if node.func.id == "exec":
                issues.append(
                    issue(
                        "AST_SECURITY_EXEC",
                        "error",
                        "security",
                        "Use of exec() detected. This allows arbitrary code execution.",
                    )
                )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and node.func.attr == "system":
                issues.append(
                    issue(
                        "AST_SECURITY_OS_SYSTEM",
                        "error",
                        "security",
                        "Use of os.system() detected. This executes shell commands.",
                    )
                )

    return issues
