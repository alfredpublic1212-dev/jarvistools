# core/structure_analyzer.py

import ast
from typing import List, Dict


def issue(rule_id: str, severity: str, category: str, message: str, confidence: str = "medium") -> Dict:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "category": category,
        "message": message,
        "confidence": confidence,
    }


class StructureVisitor(ast.NodeVisitor):
    def __init__(self):
        self.issues: List[Dict] = []
        self.nesting_depth = 0

    def generic_visit(self, node):
        is_block = isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With))

        if is_block:
            self.nesting_depth += 1

            if self.nesting_depth > 4:
                self.issues.append(
                    issue(
                        "STRUCT_DEEP_NESTING",
                        "warning",
                        "maintainability",
                        f"Deep nesting detected (depth={self.nesting_depth}). Code may be hard to read.",
                    )
                )

            super().generic_visit(node)
            self.nesting_depth -= 1
        else:
            super().generic_visit(node)


def analyze_structure(code: str) -> List[Dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = StructureVisitor()
    visitor.visit(tree)
    return visitor.issues
