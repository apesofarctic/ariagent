from ..schemas import Decision, Nudge
from ..llm import chat


class Engagement:
    def explain(self, decision: Decision) -> Nudge:
        s = decision.insight.signal
        if s.type == "overdraft_forecast":
            tool, args = "shift_debit_date", {"debit": "rent", "to_after": s.data["salary_date"]}
            label, title = "Shift rent date", "Heads up: possible overdraft"
        elif s.type == "duplicate_subscription":
            tool, args = "cancel_subscription", {"merchant": s.data["merchants"][-1]}
            label, title = "Cancel duplicate", "Duplicate subscription found"
        else:
            tool, args, label, title = "noop", {}, "Review", "Notice"

        msg = chat(
            "You write short, warm, one-line banking nudges. No emojis. Be specific.",
            f"Write a one-line nudge. Situation: {decision.insight.why}. Suggested action: {label}.",
        ) or decision.insight.why
        return Nudge(title=title, message=msg, action_label=label, tool=tool, tool_args=args)
