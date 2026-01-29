from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ScoreBreakdown:
    total: int = 0
    components: Dict[str, int] = field(default_factory=dict)
    reasons: Dict[str, str] = field(default_factory=dict)

    def add(self, name: str, value: int, reason: str = ""):
        self.total += value
        self.components[name] = self.components.get(name, 0) + value
        if reason:
            self.reasons[name] = reason


BLOCK_THRESHOLD = -100
CONFIRM_THRESHOLD = -20


def score_action(action: str, context: dict) -> ScoreBreakdown:
    s = ScoreBreakdown()
    t = action.lower()

    if "rm -rf" in t:
        s.add("destructive", -1000, "Destroys files")

    if "eval(" in t or "exec(" in t:
        s.add("unsafe", -200, "Arbitrary code execution")

    return s
