# core/taint_engine.py
import ast
import builtins
from typing import List, Dict, Set


BUILTINS = set(dir(builtins))


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


# -----------------------------
# Configuration (STRICT)
# -----------------------------

TAINT_SOURCES = {
    "input",
}

TAINT_SINK_CALLS = {
    "eval",
    "exec",
}

TAINT_SINK_ATTRS = {
    ("os", "system"),
    ("subprocess", None),  # any subprocess.*
}


class TaintVisitor(ast.NodeVisitor):
    def __init__(self):
        self.issues: List[Dict] = []

        # stack of tainted variables per scope
        self.scope_stack: List[Set[str]] = [set()]

    # -----------------------------
    # Scope helpers
    # -----------------------------
    def enter_scope(self):
        self.scope_stack.append(set())

    def exit_scope(self):
        self.scope_stack.pop()

    def is_tainted(self, name: str) -> bool:
        return any(name in scope for scope in self.scope_stack)

    def taint(self, name: str):
        self.scope_stack[-1].add(name)

    # -----------------------------
    # Function boundary
    # -----------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.enter_scope()

        # parameters are TAINT SOURCES
        for arg in node.args.args:
            self.taint(arg.arg)
            self.issues.append(
                _issue(
                    "TAINT_SOURCE",
                    "warning",
                    "security",
                    f"Function parameter '{arg.arg}' is a taint source.",
                )
            )

        for stmt in node.body:
            self.visit(stmt)

        self.exit_scope()

    # -----------------------------
    # Assignments (propagation)
    # -----------------------------
    def visit_Assign(self, node: ast.Assign):
        value_tainted = self.expr_is_tainted(node.value)

        for target in node.targets:
            if isinstance(target, ast.Name) and value_tainted:
                self.taint(target.id)
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
    # Calls (sources & sinks)
    # -----------------------------
    def visit_Call(self, node: ast.Call):
        # ---- source: input()
        if isinstance(node.func, ast.Name) and node.func.id in TAINT_SOURCES:
            parent = getattr(node, "parent", None)
            if isinstance(parent, ast.Assign):
                for target in parent.targets:
                    if isinstance(target, ast.Name):
                        self.taint(target.id)
                        self.issues.append(
                            _issue(
                                "TAINT_SOURCE",
                                "warning",
                                "security",
                                f"Variable '{target.id}' receives tainted input.",
                            )
                        )

        # ---- sink: eval / exec
        if isinstance(node.func, ast.Name) and node.func.id in TAINT_SINK_CALLS:
            for arg in node.args:
                if self.expr_is_tainted(arg):
                    self.issues.append(
                        _issue(
                            "TAINT_SINK_REACHED",
                            "error",
                            "security",
                            f"Tainted data passed to dangerous sink '{node.func.id}()'.",
                        )
                    )

        # ---- sink: os.system / subprocess.*
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            base = node.func.value.id
            attr = node.func.attr

            for sink_base, sink_attr in TAINT_SINK_ATTRS:
                if base == sink_base and (sink_attr is None or sink_attr == attr):
                    for arg in node.args:
                        if self.expr_is_tainted(arg):
                            self.issues.append(
                                _issue(
                                    "TAINT_SINK_REACHED",
                                    "error",
                                    "security",
                                    f"Tainted data passed to dangerous sink '{base}.{attr}'.",
                                )
                            )

        self.generic_visit(node)

    # -----------------------------
    # Expression taint check
    # -----------------------------
    def expr_is_tainted(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return self.is_tainted(node.id)

        if isinstance(node, ast.BinOp):
            return self.expr_is_tainted(node.left) or self.expr_is_tainted(node.right)

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in TAINT_SOURCES:
                return True

            return any(self.expr_is_tainted(arg) for arg in node.args)

        return False


# -----------------------------
# Public API
# -----------------------------
def analyze_taint(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    # attach parents (needed for source detection)
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

    visitor = TaintVisitor()
    visitor.visit(tree)
    return visitor.issues
