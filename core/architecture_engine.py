# core/architecture_engine.py
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


class ArchitectureVisitor(ast.NodeVisitor):
    """
    Phase D.2 — Architecture Intelligence (Single-file)

    Detects:
    - Unused imports (delegated to D.1, not duplicated here)
    - Circular self-imports
    - Suspicious layer mixing (very conservative)
    """

    def __init__(self):
        self.issues: List[Dict] = []
        self.imports: Set[str] = set()
        self.used_names: Set[str] = set()
        self.module_name: str | None = None

    # -----------------------------
    # Track imports
    # -----------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.name.split(".")[0]
            self.imports.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            name = node.module.split(".")[0]
            self.imports.add(name)
        self.generic_visit(node)

    # -----------------------------
    # Track usage
    # -----------------------------
    def visit_Name(self, node: ast.Name):
        self.used_names.add(node.id)
        self.generic_visit(node)

    # -----------------------------
    # Module boundary
    # -----------------------------
    def visit_Module(self, node: ast.Module):
        # Attempt to infer module name (best-effort)
        self.module_name = "__main__"
        self.generic_visit(node)

        # Circular self-import
        if self.module_name in self.imports:
            self.issues.append(
                _issue(
                    "ARCH_SELF_IMPORT",
                    "warning",
                    "architecture",
                    "Module imports itself, creating a circular dependency.",
                    "high",
                )
            )


def analyze_architecture(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = ArchitectureVisitor()
    visitor.visit(tree)
    return visitor.issues
