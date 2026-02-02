from typing import List, Dict

from core.ast_analyzer import analyze_python_ast
from core.structure_analyzer import analyze_structure
from core.complexity_engine import analyze_complexity
from core.cfg_engine import analyze_cfg
from core.dfg_engine import analyze_dfg
from core.taint_engine import analyze_taint
from core.architecture_engine import analyze_architecture
from core.resource_engine import analyze_resources
from core.fix_registry import FIX_HANDLERS
from core.scope_mapper import map_scopes, resolve_scope


DANGEROUS_PATTERNS = [
    ("rm -rf", "This command deletes files recursively and is extremely dangerous."),
    ("format c:", "This command formats a disk and destroys data."),
    ("mkfs", "This command formats a filesystem and can destroy data."),
]


class ReviewBrain:
    def __init__(self):
        print("[ReviewBrain] Initialized (analysis-only mode)")

    def review_code(self, payload: dict) -> List[Dict]:
        code = payload.get("code", "")
        language = payload.get("language", "unknown")

        results: List[Dict] = []

        # --------------------------------------------------
        # 1) Regex prefilter
        # --------------------------------------------------
        lowered = code.lower()
        for pattern, message in DANGEROUS_PATTERNS:
            if pattern in lowered:
                results.append({
                    "rule_id": "REGEX_DESTRUCTIVE_COMMAND",
                    "severity": "error",
                    "category": "security",
                    "message": message,
                    "confidence": "high",
                })

        # --------------------------------------------------
        # 2) Static analyzers
        # --------------------------------------------------
        if language.lower() in ["python", "py", "auto"]:
            results.extend(analyze_python_ast(code))
            results.extend(analyze_structure(code))
            results.extend(analyze_complexity(code))
            results.extend(analyze_cfg(code))
            results.extend(analyze_dfg(code))
            results.extend(analyze_taint(code))
            results.extend(analyze_resources(code))
            results.extend(analyze_architecture(code))

        # --------------------------------------------------
        # 3) Cleanup / suppression
        # --------------------------------------------------
        used_before_assign_vars = {
            r["message"].split("'")[1]
            for r in results
            if r["rule_id"] == "DFG_USE_BEFORE_ASSIGN"
        }

        cleaned: List[Dict] = []
        for r in results:
            if (
                r["rule_id"] == "DFG_UNUSED_VARIABLE"
                and r["message"].split("'")[1] in used_before_assign_vars
            ):
                continue
            cleaned.append(r)

        results = cleaned

        # --------------------------------------------------
        # 4) Deterministic auto-fixes (G.2)
        # --------------------------------------------------
        for issue in results:
            handler = FIX_HANDLERS.get(issue["rule_id"])
            if not handler:
                continue

            try:
                fix = handler(issue, code)
            except Exception:
                fix = None

            if fix:
                issue["fix"] = fix

        # --------------------------------------------------
        # 5) G.3 — Scope mapping
        # --------------------------------------------------
        scopes = map_scopes(code)

        for issue in results:
            loc = issue.get("location")
            if not loc:
                issue["scope"] = {"class": None, "function": None}
                continue

            issue["scope"] = resolve_scope(loc["line"], scopes)

        # --------------------------------------------------
        # 6) Clean-code fallback
        # --------------------------------------------------
        if not results:
            results.append({
                "rule_id": "CLEAN_CODE",
                "severity": "info",
                "category": "style",
                "message": "No critical issues detected by static analyzers.",
                "confidence": "low",
                "scope": {"class": None, "function": None},
            })

        return results
