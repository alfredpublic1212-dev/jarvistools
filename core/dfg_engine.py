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

        # scope stack: each entry is variables declared in that scope
        self.scope_stack: List[Set[str]] = []

        # function-local tracking
        self.assigned: Set[str] = set()
        self.used: Set[str] = set()

    # -----------------------------
    # Scope handling
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
        # reset per-function state
        self.assigned = set()
        self.used = set()

        self.enter_scope()

        # parameters are assigned
        for arg in node.args.args:
            self.assigned.add(arg.arg)
            self.current_scope().add(arg.arg)

        self.generic_visit(node)

        # unused variables (function-local only)
        for var in self.assigned:
            if var not in self.used:
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
                # shadowing: exists in outer scope
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

                self.assigned.add(target.id)
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

            self.used.add(node.id)

            if node.id not in self.assigned:
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
