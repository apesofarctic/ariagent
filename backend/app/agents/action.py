from ..schemas import Nudge
from ..tools import execute, prepare
from ..guardrails import check


class ActionAgent:
    def act(self, nudge: Nudge, profile: dict, prepare_only: bool = False) -> dict:
        ok, reason = check(nudge, profile)
        if not ok:
            return {"executed": False, "prepared": False, "reason": reason}
        if prepare_only:
            # Real-data mode never executes: produce a ready-to-approve
            # instruction the user completes in their own bank app.
            instruction, deep_link = prepare(nudge.tool, nudge.tool_args)
            return {"executed": False, "prepared": True,
                    "result": instruction, "deep_link": deep_link}
        return {"executed": True, "prepared": False,
                "result": execute(nudge.tool, nudge.tool_args)}
