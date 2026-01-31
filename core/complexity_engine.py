# core/complexity_engine.py

import ast
from typing import List, Dict


def issue(rule_id: str, severity: str, category: str, message: str, confidence: str = "medium") -> Dict:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "category": category,
        "message": message,
        "confidence": confidence,
    }


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.issues: List[Dict] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        complexity = 1
        statement_count = len(node.body)
        param_count = len(node.args.args)

        for n in ast.walk(node):
            if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(n, ast.BoolOp):
                complexity += len(n.values) - 1

        # Cyclomatic complexity
        if complexity > 12:
            self.issues.append(
                issue(
                    "COMPLEXITY_CYCLOMATIC_HIGH",
                    "warning",
                    "maintainability",
                    f"High cyclomatic complexity in function '{node.name}' (score={complexity}).",
                    "high",
                )
            )
        elif complexity > 7:
            self.issues.append(
                issue(
                    "COMPLEXITY_CYCLOMATIC_MODERATE",
                    "warning",
                    "maintainability",
                    f"Moderate cyclomatic complexity in function '{node.name}' (score={complexity}).",
                )
            )

        # Function size
        if statement_count > 75:
            self.issues.append(
                issue(
                    "STRUCT_FUNCTION_VERY_LARGE",
                    "warning",
                    "maintainability",
                    f"Function '{node.name}' is very large ({statement_count} statements).",
                    "high",
                )
            )
        elif statement_count > 40:
            self.issues.append(
                issue(
                    "STRUCT_FUNCTION_LARGE",
                    "warning",
                    "maintainability",
                    f"Function '{node.name}' is large ({statement_count} statements).",
                )
            )

        # Parameter count
        if param_count > 8:
            self.issues.append(
                issue(
                    "DESIGN_TOO_MANY_PARAMS",
                    "warning",
                    "design",
                    f"Function '{node.name}' has too many parameters ({param_count}).",
                    "high",
                )
            )
        elif param_count > 5:
            self.issues.append(
                issue(
                    "DESIGN_MANY_PARAMS",
                    "warning",
                    "design",
                    f"Function '{node.name}' has many parameters ({param_count}).",
                )
            )

        self.generic_visit(node)


def analyze_complexity(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = ComplexityVisitor()
    visitor.visit(tree)
    return visitor.issues
