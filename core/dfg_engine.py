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
    SMART REALISTIC DFG ENGINE
    Designed for real dev experience (Cursor-like)

    Detects:
    - REAL use-before-assign only
    - REAL unused variables only
    Avoids:
    - loop variable false flags
    - import usage false flags
    - class/function scope confusion
    """

    def __init__(self, source_lines: list[str]):
        self.issues: List[Dict] = []
        self.source_lines = source_lines

        self.scope_stack: List[Set[str]] = [set()]
        self.assigned_stack: List[Set[str]] = [set()]
        self.used_stack: List[Set[str]] = [set()]

        self.imported: Set[str] = set()
        self.defined_funcs: Set[str] = set()
        self.defined_classes: Set[str] = set()

    # -------------------------
    # scope helpers
    # -------------------------
    def enter_scope(self):
        self.scope_stack.append(set())
        self.assigned_stack.append(set())
        self.used_stack.append(set())

    def exit_scope(self):
        assigned = self.assigned_stack.pop()
        used = self.used_stack.pop()
        self.scope_stack.pop()

        # detect real unused vars
        for var in assigned:
            if var not in used:
                if var.startswith("_"):
                    continue
                if var in self.imported:
                    continue
                if var in self.defined_funcs:
                    continue
                if var in self.defined_classes:
                    continue

                self.issues.append(
                    _issue(
                        "DFG_UNUSED_VARIABLE",
                        "warning",
                        "maintainability",
                        f"Variable '{var}' is assigned but never used.",
                        "medium",
                    )
                )

    def declare(self, name: str):
        self.scope_stack[-1].add(name)
        self.assigned_stack[-1].add(name)

    def mark_used(self, name: str):
        for used in reversed(self.used_stack):
            used.add(name)
            break

    def is_declared(self, name: str) -> bool:
        return any(name in scope for scope in self.scope_stack)

    # -------------------------
    # imports
    # -------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.declare(name)
            self.imported.add(name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            name = alias.asname or alias.name
            self.declare(name)

    # -------------------------
    # class
    # -------------------------
    def visit_ClassDef(self, node: ast.ClassDef):
        self.declare(node.name)
        self.defined_classes.add(node.name)

        self.enter_scope()
        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    # -------------------------
    # function
    # -------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.declare(node.name)
        self.defined_funcs.add(node.name)

        self.enter_scope()

        for arg in node.args.args:
            self.declare(arg.arg)

        for stmt in node.body:
            self.visit(stmt)

        self.exit_scope()

    # -------------------------
    # with open() as f
    # -------------------------
    def visit_With(self, node: ast.With):
        for item in node.items:
            if isinstance(item.optional_vars, ast.Name):
                self.declare(item.optional_vars.id)
        self.generic_visit(node)

    # -------------------------
    # assignment
    # -------------------------
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.declare(target.id)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        if isinstance(node.target, ast.Name):
            self.declare(node.target.id)
        self.generic_visit(node)

    # -------------------------
    # usage
    # -------------------------
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            name = node.id

            if name in BUILTINS:
                return

            if self.is_declared(name):
                self.mark_used(name)
                return

            if name in self.defined_funcs or name in self.defined_classes:
                return

            if name in self.imported:
                return

            # real undefined only
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

    visitor = DFGVisitor(code.splitlines())
    visitor.visit(tree)
    return visitor.issues