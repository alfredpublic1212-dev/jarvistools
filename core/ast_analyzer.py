import ast
from typing import List, Dict


def _issue(
    rule_id: str,
    severity: str,
    category: str,
    message: str,
    confidence: str = "high",
) -> Dict:
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
            _issue(
                rule_id="AST_SYNTAX_ERROR",
                severity="error",
                category="syntax",
                message=f"Syntax error: {e.msg} (line {e.lineno})",
                confidence="high",
            )
        ]

    for node in ast.walk(tree):

        # Infinite loop
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                if not has_break:
                    issues.append(
                        _issue(
                            "AST_INFINITE_LOOP",
                            "warning",
                            "performance",
                            "Possible infinite loop detected: 'while True' without break.",
                            "high",
                        )
                    )

        # Bare / empty except
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append(
                    _issue(
                        "AST_BARE_EXCEPT",
                        "warning",
                        "bug",
                        "Bare except detected. This catches SystemExit, KeyboardInterrupt, etc.",
                        "high",
                    )
                )
            elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                issues.append(
                    _issue(
                        "AST_EMPTY_EXCEPT",
                        "warning",
                        "bug",
                        "Empty except block detected. Exception is silently ignored.",
                        "medium",
                    )
                )

        # eval / exec
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "eval":
                issues.append(
                    _issue(
                        "AST_EVAL_EXECUTION",
                        "error",
                        "security",
                        "Use of eval() detected. This allows arbitrary code execution.",
                        "high",
                    )
                )
            if node.func.id == "exec":
                issues.append(
                    _issue(
                        "AST_EXEC_EXECUTION",
                        "error",
                        "security",
                        "Use of exec() detected. This allows arbitrary code execution.",
                        "high",
                    )
                )

        # os.system
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"
                and node.func.attr == "system"
            ):
                issues.append(
                    _issue(
                        "AST_OS_SYSTEM",
                        "error",
                        "security",
                        "Use of os.system() detected. This executes shell commands.",
                        "high",
                    )
                )

        # subprocess.*
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                issues.append(
                    _issue(
                        "AST_SUBPROCESS_CALL",
                        "error",
                        "security",
                        "Use of subprocess detected. This can execute external commands.",
                        "high",
                    )
                )

        # File writes
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "open" and len(node.args) >= 2:
                mode_node = node.args[1]
                if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
                    if any(m in mode_node.value for m in ["w", "a", "+"]):
                        issues.append(
                            _issue(
                                "AST_FILE_WRITE",
                                "warning",
                                "security",
                                "File write operation detected. This can overwrite or modify files.",
                                "medium",
                            )
                        )

    return issues
