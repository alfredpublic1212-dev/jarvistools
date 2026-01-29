#core/ethics.py
from dataclasses import dataclass

@dataclass
class EthicsDecision:
    allow: bool
    severity: str
    score: int
    reason: str
    requires_confirm: bool = False


def evaluate_ethics(action: str, context: dict) -> EthicsDecision:
    text = action.lower()

    if any(x in text for x in ["rm -rf", "delete all", "format disk"]):
        return EthicsDecision(
            allow=False,
            severity="HARD",
            score=-1000,
            reason="Destructive action detected.",
            requires_confirm=False,
        )

    return EthicsDecision(
        allow=True,
        severity="OK",
        score=0,
        reason="No ethical violations.",
        requires_confirm=False,
    )
