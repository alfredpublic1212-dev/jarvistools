# core/taint_engine.py
import ast
import builtins
from typing import List, Dict, Set

BUILTINS = set(dir(builtins))

TAINT_SOURCES = {
    "input",
}

TAINT_SINKS = {
    "eval",
    "exec",
    "os.system",
}


def _issue(
    rule_id: str,
    severity: str,
    category: str,
    message: str,
    confidence: str = "high",
) -> Dict:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "category": category,
        "message": message,
        "confidence": confidence,
    }


class TaintVisitor(ast.NodeVisitor):
    """
    Phase C.3 — Minimal, Correct Taint Tracking

    Implements:
    - Taint creation
    - Taint propagation
    - Taint sink detection

    Explicitly NOT:
    - Interprocedural
    - Multi-file
    - Framework-specific
    """

    def __init__(self):
        self.issues: List[Dict] = []

        # stack of scopes: global → function → nested
        self.scope_stack: List[Set[str]] = [set()]

        # tainted variables
        self.tainted: Set[str] = set()

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
    # Imports are safe assignments
    # -----------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.current_scope().add(alias.asname or alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            self.current_scope().add(alias.asname or alias.name)

    # -----------------------------
    # Function boundary
    # -----------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.enter_scope()

        # parameters are NOT tainted by default
        for arg in node.args.args:
            self.current_scope().add(arg.arg)

        for stmt in node.body:
            self.visit(stmt)

        self.exit_scope()

    # -----------------------------
    # Assignments
    # -----------------------------
    def visit_Assign(self, node: ast.Assign):
        value_is_source = self.is_direct_source(node.value)
        value_is_tainted = self.expr_is_tainted(node.value)

        for target in node.targets:
            if isinstance(target, ast.Name):
                self.current_scope().add(target.id)

                # Direct source assignment
                if value_is_source:
                    self.tainted.add(target.id)
                    self.issues.append(
                        _issue(
                            "TAINT_SOURCE",
                            "warning",
                            "security",
                            f"Variable '{target.id}' receives tainted input.",
                        )
                    )

                # Propagation ONLY if coming from another tainted variable
                elif value_is_tainted:
                    self.tainted.add(target.id)
                    self.issues.append(
                        _issue(
                            "TAINT_PROPAGATION",
                            "warning",
                            "security",
                            f"Taint propagated to variable '{target.id}'.",
                        )
                    )

        self.generic_visit(node)

    # -----------------------------
    # Sink detection
    # -----------------------------
    def visit_Call(self, node: ast.Call):
        sink_name = self.get_sink_name(node)

        if sink_name and any(self.expr_is_tainted(arg) for arg in node.args):
            self.issues.append(
                _issue(
                    "TAINT_SINK_REACHED",
                    "error",
                    "security",
                    f"Tainted data passed to dangerous sink '{sink_name}'.",
                )
            )

        self.generic_visit(node)

    # -----------------------------
    # Helpers
    # -----------------------------
    def is_direct_source(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in TAINT_SOURCES
        )

    def expr_is_tainted(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id in self.tainted

        if isinstance(node, ast.BinOp):
            return self.expr_is_tainted(node.left) or self.expr_is_tainted(node.right)

        if isinstance(node, ast.Call):
            return any(self.expr_is_tainted(arg) for arg in node.args)

        return False

    def get_sink_name(self, node: ast.Call) -> str | None:
        if isinstance(node.func, ast.Name) and node.func.id in TAINT_SINKS:
            return node.func.id

        if isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and f"{node.func.value.id}.{node.func.attr}" in TAINT_SINKS
            ):
                return f"{node.func.value.id}.{node.func.attr}"

        return None


def analyze_taint(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = TaintVisitor()
    visitor.visit(tree)
    return visitor.issues
