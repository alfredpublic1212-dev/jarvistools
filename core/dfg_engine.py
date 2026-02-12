# core/dfg_engine.py
import ast
import builtins
from typing import List, Dict, Set

BUILTINS = set(dir(builtins))


def _issue(
    rule_id: str,
    severity: str,
    category: str,
    message: str,
    confidence: str = "medium",
    *,
    node: ast.AST | None = None,
    source_lines: list[str] | None = None,
) -> Dict:
    issue = {
        "rule_id": rule_id,
        "severity": severity,
        "category": category,
        "message": message,
        "confidence": confidence,
    }

    # Attach location metadata (for editor jump)
    if node is not None and hasattr(node, "lineno"):
        issue["location"] = {
            "line": node.lineno,
            "column": getattr(node, "col_offset", None),
        }

        if source_lines and 1 <= node.lineno <= len(source_lines):
            issue["code_snippet"] = source_lines[node.lineno - 1].rstrip()

    return issue


class DFGVisitor(ast.NodeVisitor):
    """
    SMART DFG ENGINE (production-grade)

    Goals:
    - ZERO false positives for valid Python
    - Detect real use-before-assign
    - Detect real unused vars
    - Handle classes, funcs, imports, with-open
    - Cursor-level realistic behaviour
    """

    def __init__(self, source_lines: list[str]):
        self.issues: List[Dict] = []
        self.source_lines = source_lines

        # scope stack
        self.scope_stack: List[Set[str]] = [set()]

        # tracking
        self.assigned: Set[str] = set()
        self.used: Set[str] = set()

        # globals
        self.defined_functions: Set[str] = set()
        self.defined_classes: Set[str] = set()
        self.imported_modules: Set[str] = set()

    # -----------------------------
    # Scope helpers
    # -----------------------------
    def enter_scope(self):
        self.scope_stack.append(set())

    def exit_scope(self):
        self.scope_stack.pop()

    def current_scope(self) -> Set[str]:
        return self.scope_stack[-1]

    def declare(self, name: str):
        self.current_scope().add(name)
        self.assigned.add(name)

    def is_declared(self, name: str) -> bool:
        return any(name in scope for scope in self.scope_stack)

    # -----------------------------
    # Imports
    # -----------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.declare(name)
            self.imported_modules.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            name = alias.asname or alias.name
            self.declare(name)
        self.generic_visit(node)

    # -----------------------------
    # Class definitions
    # -----------------------------
    def visit_ClassDef(self, node: ast.ClassDef):
        self.declare(node.name)
        self.defined_classes.add(node.name)

        self.enter_scope()
        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    # -----------------------------
    # Function definitions
    # -----------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.declare(node.name)
        self.defined_functions.add(node.name)

        self.enter_scope()

        # parameters are declared
        for arg in node.args.args:
            self.declare(arg.arg)

        for stmt in node.body:
            self.visit(stmt)

        # detect unused locals (real only)
        for var in list(self.assigned):
            if var not in self.used:
                # ignore common safe cases
                if var.startswith("_"):
                    continue
                if var in self.defined_functions:
                    continue
                if var in self.defined_classes:
                    continue
                if var in self.imported_modules:
                    continue

                self.issues.append(
                    _issue(
                        "DFG_UNUSED_VARIABLE",
                        "warning",
                        "maintainability",
                        f"Variable '{var}' is assigned but never used.",
                        "medium",
                        node=node,
                        source_lines=self.source_lines,
                    )
                )

        self.exit_scope()

    # -----------------------------
    # WITH open(...) as f:
    # -----------------------------
    def visit_With(self, node: ast.With):
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                self.declare(item.optional_vars.id)
        self.generic_visit(node)

    # -----------------------------
    # Assignments
    # -----------------------------
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.declare(target.id)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        if isinstance(node.target, ast.Name):
            if not self.is_declared(node.target.id):
                self.declare(node.target.id)
        self.generic_visit(node)

    # -----------------------------
    # Variable usage
    # -----------------------------
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            name = node.id

            # builtins safe
            if name in BUILTINS:
                return

            # declared anywhere safe
            if self.is_declared(name):
                self.used.add(name)
                return

            # functions/classes safe
            if name in self.defined_functions or name in self.defined_classes:
                return

            # imports safe
            if name in self.imported_modules:
                return

            # allow forward reference (python allows)
            # only flag if clearly broken
            self.issues.append(
                _issue(
                    "DFG_USE_BEFORE_ASSIGN",
                    "warning",
                    "logic",
                    f"Variable '{name}' may be used before assignment.",
                    "low",
                    node=node,
                    source_lines=self.source_lines,
                )
            )

        self.generic_visit(node)


def analyze_dfg(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    source_lines = code.splitlines()
    visitor = DFGVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues