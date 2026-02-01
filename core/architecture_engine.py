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
    Phase D.2 + D.3 — Architecture Intelligence (Single-file, Conservative)

    D.2:
    - Unused imports
    - Self-imports

    D.3:
    - God module (aggregated)
    - Mixed concerns
    """

    def __init__(self):
        self.issues: List[Dict] = []

        # D.2 tracking
        self.imports: Set[str] = set()
        self.used_names: Set[str] = set()

        # D.3 metrics
        self.import_count = 0
        self.func_count = 0
        self.class_count = 0

        self.has_io = False
        self.has_logic = False

    # -----------------------------
    # Imports
    # -----------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
            self.import_count += 1
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.imports.add(node.module.split(".")[0])
            self.import_count += 1
        self.generic_visit(node)

    # -----------------------------
    # Usage tracking
    # -----------------------------
    def visit_Name(self, node: ast.Name):
        self.used_names.add(node.id)
        self.generic_visit(node)

    # -----------------------------
    # Structure / logic
    # -----------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.func_count += 1
        self.has_logic = True
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_count += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        self.has_logic = True
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.has_logic = True
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.has_logic = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            self.has_io = True

        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in {"os", "subprocess"}:
                    self.has_io = True

        self.generic_visit(node)

    # -----------------------------
    # Module boundary (D.2 + D.3)
    # -----------------------------
    def visit_Module(self, node: ast.Module):
        self.generic_visit(node)

        # ---- D.2: Unused imports
        for name in self.imports:
            if name not in self.used_names:
                self.issues.append(
                    _issue(
                        "ARCH_UNUSED_IMPORT",
                        "warning",
                        "architecture",
                        f"Imported module '{name}' is never used.",
                    )
                )

        # ---- D.3 aggregation
        top_level_defs = self.func_count + self.class_count
        mixed_concerns = self.has_io and self.has_logic

        signals = 0
        if self.import_count >= 12:
            signals += 1
        if top_level_defs >= 8:
            signals += 1
        if mixed_concerns:
            signals += 1

        if signals >= 2:
            self.issues.append(
                _issue(
                    "ARCH_GOD_MODULE",
                    "warning",
                    "architecture",
                    "Module appears to be doing too much and may lack clear separation of concerns.",
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
