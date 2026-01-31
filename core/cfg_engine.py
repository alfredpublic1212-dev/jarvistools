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
    """
    Phase C.1 — Minimal CFG Engine

    Guarantees:
    - No false positives
    - Block-aware only
    - No path explosion
    """

    def __init__(self):
        self.issues: List[Dict] = []

    # -----------------------------
    # Function-level CFG
    # -----------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        for idx, stmt in enumerate(node.body):

            # Dead code after return
            if isinstance(stmt, ast.Return) and idx + 1 < len(node.body):
                self.issues.append(
                    _issue(
                        "CFG_DEAD_AFTER_RETURN",
                        "warning",
                        "logic",
                        f"Code after return statement in function '{node.name}' is unreachable.",
                        "medium",
                    )
                )

            # Dead code after raise
            if isinstance(stmt, ast.Raise) and idx + 1 < len(node.body):
                self.issues.append(
                    _issue(
                        "CFG_DEAD_AFTER_RAISE",
                        "warning",
                        "logic",
                        f"Code after raise statement in function '{node.name}' is unreachable.",
                        "medium",
                    )
                )

        self.generic_visit(node)

    # -----------------------------
    # Branch-level CFG
    # -----------------------------
    def visit_If(self, node: ast.If):
        # Constant false branch
        if isinstance(node.test, ast.Constant) and node.test.value is False:
            self.issues.append(
                _issue(
                    "CFG_DEAD_BRANCH_LITERAL",
                    "warning",
                    "logic",
                    "Branch guarded by constant False is unreachable.",
                    "medium",
                )
            )

        self.generic_visit(node)

    # -----------------------------
    # Loop-level CFG
    # -----------------------------
    def visit_While(self, node: ast.While):
        # Confirmed infinite loop
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            has_exit = any(
                isinstance(n, (ast.Break, ast.Return, ast.Raise))
                for n in ast.walk(node)
            )
            if not has_exit:
                self.issues.append(
                    _issue(
                        "CFG_INFINITE_LOOP_CONFIRMED",
                        "warning",
                        "logic",
                        "Control-flow confirms infinite loop with no exit path.",
                        "high",
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
