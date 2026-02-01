# core/resource_engine.py
import ast
from typing import List, Dict, Set


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


class ResourceVisitor(ast.NodeVisitor):
    """
    Phase C.4 — Resource Semantics (Conservative)

    Detects:
    - open() used outside of `with`
    - open() without explicit close()
    """

    def __init__(self):
        self.issues: List[Dict] = []

        # track variables assigned from open()
        self.opened_files: Set[str] = set()

        # track variables that get closed
        self.closed_files: Set[str] = set()

        # track open() used inside with
        self.with_open_lines: Set[int] = set()

    # -----------------------------
    # with open(...) as f:
    # -----------------------------
    def visit_With(self, node: ast.With):
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Name):
                    if item.context_expr.func.id == "open":
                        self.with_open_lines.add(node.lineno)
        self.generic_visit(node)

    # -----------------------------
    # f = open(...)
    # -----------------------------
    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id == "open":
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.opened_files.add(target.id)
        self.generic_visit(node)

    # -----------------------------
    # f.close()
    # -----------------------------
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "close":
                if isinstance(node.func.value, ast.Name):
                    self.closed_files.add(node.func.value.id)
        self.generic_visit(node)

    # -----------------------------
    # Final evaluation
    # -----------------------------
    def visit_Module(self, node: ast.Module):
        self.generic_visit(node)

        for var in self.opened_files:
            if var not in self.closed_files:
                self.issues.append(
                    _issue(
                        "RESOURCE_FILE_NOT_CLOSED",
                        "warning",
                        "resource",
                        f"File object '{var}' opened but never closed.",
                        "medium",
                    )
                )


def analyze_resources(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = ResourceVisitor()
    visitor.visit(tree)
    return visitor.issues
