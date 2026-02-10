# core/scope_mapper.py
import ast
from typing import List, Dict


class ScopeMapper(ast.NodeVisitor):
    """
    Deterministic scope mapper.
    Maps line numbers → class / function.
    """

    def __init__(self):
        self.scopes: List[Dict] = []
        self.class_stack: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_stack.append(node.name)

        self.scopes.append({
            "type": "class",
            "name": node.name,
            "start": node.lineno,
            "end": getattr(node, "end_lineno", node.lineno),
        })

        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.scopes.append({
            "type": "function",
            "name": node.name,
            "class": self.class_stack[-1] if self.class_stack else None,
            "start": node.lineno,
            "end": getattr(node, "end_lineno", node.lineno),
        })

        self.generic_visit(node)


def map_scopes(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    mapper = ScopeMapper()
    mapper.visit(tree)
    return mapper.scopes


def resolve_scope(line: int, scopes: List[Dict]) -> Dict:
    """
    Resolve innermost scope for a line.
    Preference: function > class.
    """
    matches = [
        s for s in scopes
        if s["start"] <= line <= s["end"]
    ]

    for s in matches:
        if s["type"] == "function":
            return {
                "class": s.get("class"),
                "function": s["name"]
            }

    for s in matches:
        if s["type"] == "class":
            return {
                "class": s["name"],
                "function": None
            }

    return {
        "class": None,
        "function": None
    }
