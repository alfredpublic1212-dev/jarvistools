# core/cfg_engine.py
import ast
from typing import List, Dict


def _issue(
    rule_id: str,
    severity: str,
    category: str,
    message: str,
    confidence: str = "medium",
) -> Dict:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "category": category,
        "message": message,
        "confidence": confidence,
    }


class CFGVisitor(ast.NodeVisitor):
    def __init__(self):
        self.issues: List[Dict] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        returns = []
        unreachable_found = False

        for idx, stmt in enumerate(node.body):
            if isinstance(stmt, ast.Return):
                returns.append(stmt)
                if idx < len(node.body) - 1:
                    unreachable_found = True

        # Dead code after return
        if unreachable_found:
            self.issues.append(
                _issue(
                    "CFG_DEAD_AFTER_RETURN",
                    "warning",
                    "logic",
                    f"Code after return statement in function '{node.name}' is unreachable.",
                )
            )

        # Multiple returns
        if len(returns) > 1:
            self.issues.append(
                _issue(
                    "CFG_MULTIPLE_RETURNS",
                    "info",
                    "design",
                    f"Function '{node.name}' has multiple return paths ({len(returns)}).",
                )
            )

        # No guaranteed exit
        if not returns:
            self.issues.append(
                _issue(
                    "CFG_NO_GUARANTEED_EXIT",
                    "warning",
                    "logic",
                    f"Function '{node.name}' has no guaranteed return statement.",
                )
            )

        self.generic_visit(node)


def analyze_cfg(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = CFGVisitor()
    visitor.visit(tree)
    return visitor.issues
