import ast
from typing import List, Dict, Set

TAINT_SOURCES = {"input"}
TAINT_SINKS = {"eval", "exec", "os.system"}


def _issue(rule_id, severity, category, message, confidence="high"):
    return {
        "rule_id": rule_id,
        "severity": severity,
        "category": category,
        "message": message,
        "confidence": confidence,
    }


class TaintVisitor(ast.NodeVisitor):
    """
    REALISTIC TAINT ENGINE
    Only warns when input reaches dangerous sink.
    Not spammy.
    """

    def __init__(self):
        self.issues: List[Dict] = []
        self.tainted: Set[str] = set()

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                if node.value.func.id in TAINT_SOURCES:
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            self.tainted.add(t.id)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        sink = None

        if isinstance(node.func, ast.Name):
            if node.func.id in TAINT_SINKS:
                sink = node.func.id

        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                full = f"{node.func.value.id}.{node.func.attr}"
                if full in TAINT_SINKS:
                    sink = full

        if sink:
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in self.tainted:
                    self.issues.append(
                        _issue(
                            "TAINT_SINK_REACHED",
                            "error",
                            "security",
                            f"Tainted input reaches dangerous sink '{sink}'.",
                        )
                    )

        self.generic_visit(node)


def analyze_taint(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = TaintVisitor()
    visitor.visit(tree)
    return visitor.issues