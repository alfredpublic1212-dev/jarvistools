class GuardDecision:
    def __init__(self, allow: bool, require_confirm: bool = False, message: str = ""):
        self.allow = allow
        self.require_confirm = require_confirm
        self.message = message


def security_guard(text: str, is_confirmed: bool):
    t = text.lower()

    if any(x in t for x in ["rm -rf", "format", "wipe"]):
        return GuardDecision(False, False, "Dangerous command blocked.")

    return GuardDecision(True)
