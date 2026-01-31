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

        # scope stack: global -> function -> nested
        self.scope_stack: List[Set[str]] = [set()]

        # function-local tracking
        self.local_assigned: Set[str] = set()
        self.local_used: Set[str] = set()

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
        self.enter_scope()

        self.local_assigned = set()
        self.local_used = set()

        # parameters are assigned
        for arg in node.args.args:
            self.local_assigned.add(arg.arg)
            self.current_scope().add(arg.arg)

        # walk body
        for stmt in node.body:
            self.visit(stmt)

        # unused locals ONLY
        for var in self.local_assigned:
            if var not in self.local_used:
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

                # shadowing
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

                self.local_assigned.add(target.id)
                self.current_scope().add(target.id)

        self.generic_visit(node)

    # -----------------------------
    # Variable usage
    # -----------------------------
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):

            # ignore builtins
            if node.id in BUILTINS:
                return

            # used before assign
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
            else:
                self.local_used.add(node.id)

        self.generic_visit(node)


def analyze_dfg(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = DFGVisitor()
    visitor.visit(tree)
    return visitor.issues
