#   core/dfg_engine.py
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


class DFGVisitor(ast.NodeVisitor):
    def __init__(self):
        self.issues: List[Dict] = []

        # stack of scopes, each scope is a set of variable names
        self.scope_stack: List[Set[str]] = []

        # 🔧 FIX 1: initialize GLOBAL scope
        self.scope_stack.append(set())

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
    # Function boundary
    # -----------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        # 🔧 FIX 2: function-local tracking
        self.enter_scope()

        local_assigned: Set[str] = set()
        local_used: Set[str] = set()

        # parameters are considered assigned
        for arg in node.args.args:
            local_assigned.add(arg.arg)
            self.current_scope().add(arg.arg)

        # walk body manually
        for stmt in node.body:
            self.visit(stmt)

        # unused variable detection (LOCAL ONLY)
        for var in local_assigned:
            if var not in local_used:
                self.issues.append(
                    _issue(
                        "DFG_UNUSED_VARIABLE",
                        "warning",
                        "maintainability",
                        f"Variable '{var}' is assigned but never used.",
                        "medium",
                    )
                )

        self.exit_scope()

    # -----------------------------
    # Assignments
    # -----------------------------
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):

                # 🔧 FIX 3: variable shadowing (outer scope)
                for scope in self.scope_stack[:-1]:
                    if target.id in scope:
                        self.issues.append(
                            _issue(
                                "DFG_VARIABLE_SHADOWING",
                                "warning",
                                "design",
                                f"Variable '{target.id}' shadows a variable from an outer scope.",
                                "medium",
                            )
                        )

                # record assignment in current scope
                self.current_scope().add(target.id)

        self.generic_visit(node)

    # -----------------------------
    # Variable usage
    # -----------------------------
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):

            # 🔧 FIX 4: ignore builtins, check real scopes only
            if not any(node.id in scope for scope in self.scope_stack):
                self.issues.append(
                    _issue(
                        "DFG_USE_BEFORE_ASSIGN",
                        "warning",
                        "logic",
                        f"Variable '{node.id}' is used before assignment.",
                        "high",
                    )
                )

        self.generic_visit(node)


def analyze_dfg(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = DFGVisitor()
    visitor.visit(tree)
    return visitor.issues
