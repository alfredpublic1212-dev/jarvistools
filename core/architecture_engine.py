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
    def __init__(self):
        self.issues: List[Dict] = []

        self.imports: Set[str] = set()
        self.used_names: Set[str] = set()
        self.module_name: str | None = None

    # -----------------------------
    # Module context
    # -----------------------------
    def visit_Module(self, node: ast.Module):
        self.generic_visit(node)

        # unused imports
        for name in self.imports:
            if name not in self.used_names:
                self.issues.append(
                    _issue(
                        "ARCH_UNUSED_IMPORT",
                        "warning",
                        "architecture",
                        f"Imported module '{name}' is never used.",
                        "medium",
                    )
                )

    # -----------------------------
    # import x
    # -----------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.add(alias.asname or alias.name.split(".")[0])

    # -----------------------------
    # from x import y
    # -----------------------------
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base = node.module.split(".")[0]
            for alias in node.names:
                self.imports.add(alias.asname or alias.name)

                # self-import (single-file safe heuristic)
                if alias.name == base:
                    self.issues.append(
                        _issue(
                            "ARCH_SELF_IMPORT",
                            "warning",
                            "architecture",
                            f"Module imports itself via '{node.module}'.",
                            "high",
                        )
                    )

    # -----------------------------
    # usage tracking
    # -----------------------------
    def visit_Name(self, node: ast.Name):
        self.used_names.add(node.id)
        self.generic_visit(node)


def analyze_architecture(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = ArchitectureVisitor()
    visitor.visit(tree)
    return visitor.issues
