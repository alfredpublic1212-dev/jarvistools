from dataclasses import dataclass
from core.ethics import evaluate_ethics
from core.guard import security_guard
from core.score_engine import score_action, BLOCK_THRESHOLD, CONFIRM_THRESHOLD

@dataclass
class Decision:
    allow: bool
    require_confirm: bool = False
    reason: str = ""


def evaluate(action: str, context: dict, is_confirmed: bool = False) -> Decision:
    eth = evaluate_ethics(action, context)
    if not eth.allow:
        return Decision(False, reason=eth.reason)

    sec = security_guard(action, is_confirmed)
    if not sec.allow:
        return Decision(False, reason=sec.message)

    score = score_action(action, context)

    if score.total <= BLOCK_THRESHOLD:
        return Decision(False, reason="Catastrophic long-term risk.")

    if score.total < CONFIRM_THRESHOLD and not is_confirmed:
        return Decision(False, require_confirm=True, reason="High risk action.")

    return Decision(True, reason="Allowed.")
