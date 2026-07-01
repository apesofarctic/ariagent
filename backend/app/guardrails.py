from .schemas import Nudge

REVERSIBLE = {"shift_debit_date", "cancel_subscription", "open_goal", "start_sip"}


def check(nudge: Nudge, profile: dict) -> tuple[bool, str]:
    if not profile.get("consent", False):
        return False, "no consent on file"
    if nudge.tool not in REVERSIBLE:
        return False, "action not reversible — needs manual confirmation"
    return True, "ok"
