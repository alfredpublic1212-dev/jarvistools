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

    # -----------------------------
    # Location metadata (BEST-EFFORT)
    # -----------------------------
    if node is not None and hasattr(node, "lineno"):
        issue["location"] = {
            "line": node.lineno,
            "column": getattr(node, "col_offset", None),
        }

        if source_lines and 1 <= node.lineno <= len(source_lines):
            issue["code_snippet"] = source_lines[node.lineno - 1].rstrip()

    return issue


class DFGVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: list[str]):
        self.issues: List[Dict] = []

        # scope stack: global → function → nested
        self.scope_stack: List[Set[str]] = [set()]

        # function-local tracking
        self.local_assigned: Set[str] = set()
        self.local_used: Set[str] = set()

        self.source_lines = source_lines

    # -----------------------------
    # Scope helpers
    # -----------------------------
    def enter_scope(self):
        self.scope_stack.append(set())

    def exit_scope(self):
        self.scope_stack.pop()

    def current_scope(self) -> Set[str]:
        return self.scope_stack[-1]

    # -----------------------------
    # IMPORTS CREATE BINDINGS
    # -----------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.scope_stack[0].add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            name = alias.asname or alias.name
            self.scope_stack[0].add(name)
        self.generic_visit(node)

    # -----------------------------
    # Function boundary
    # -----------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.enter_scope()

        self.local_assigned = set()
        self.local_used = set()

        # parameters are assigned
        for arg in node.args.args:
            self.local_assigned.add(arg.arg)
            self.current_scope().add(arg.arg)

        for stmt in node.body:
            self.visit(stmt)

        # unused locals
        for var in self.local_assigned:
            if var not in self.local_used:
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
    # Assignments
    # -----------------------------
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                for scope in self.scope_stack[:-1]:
                    if target.id in scope:
                        self.issues.append(
                            _issue(
                                "DFG_VARIABLE_SHADOWING",
                                "warning",
                                "design",
                                f"Variable '{target.id}' shadows a variable from an outer scope.",
                                "medium",
                                node=target,
                                source_lines=self.source_lines,
                            )
                        )

                self.local_assigned.add(target.id)
                self.current_scope().add(target.id)

        self.generic_visit(node)

    # -----------------------------
    # Variable usage
    # -----------------------------
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            if node.id in BUILTINS:
                return

            if not any(node.id in scope for scope in self.scope_stack):
                self.issues.append(
                    _issue(
                        "DFG_USE_BEFORE_ASSIGN",
                        "warning",
                        "logic",
                        f"Variable '{node.id}' is used before assignment.",
                        "high",
                        node=node,
                        source_lines=self.source_lines,
                    )
                )
            else:
                self.local_used.add(node.id)

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
