from ..schemas import Nudge
from ..tools import execute
from ..guardrails import check


class ActionAgent:
    def act(self, nudge: Nudge, profile: dict) -> dict:
        ok, reason = check(nudge, profile)
        if not ok:
            return {"executed": False, "reason": reason}
        return {"executed": True, "result": execute(nudge.tool, nudge.tool_args)}
