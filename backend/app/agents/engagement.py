from ..schemas import Decision, Nudge
from ..llm import chat


class Engagement:
    def explain(self, decision: Decision) -> Nudge:
        s = decision.insight.signal
        regulated, journey = False, None
        if s.type == "overdraft_forecast":
            tool, args = "shift_debit_date", {"debit": "rent", "to_after": s.data["salary_date"]}
            label, title = "Shift rent date", "Heads up: possible overdraft"
        elif s.type == "duplicate_subscription":
            tool, args = "cancel_subscription", {"merchant": s.data["merchants"][-1]}
            label, title = "Cancel duplicate", "Duplicate subscription found"
        elif s.type == "salary_hike":
            tool, args = "start_sip", {"amount": s.data["sip_suggestion"]}
            label = f"Start SIP of Rs{s.data['sip_suggestion']:,}/mo"
            title = "Your salary went up"
            regulated = True
        elif s.type == "life_event_baby":
            tool, args = "open_goal", {"name": "Little One Fund"}
            label, title = "Start the journey", "A new chapter?"
            journey = [
                "Top up your emergency fund to 6 months of expenses",
                "Review your health insurance cover (via your bank's licensed partner)",
                "Open a child-goal savings plan",
            ]
        else:
            tool, args, label, title = "noop", {}, "Review", "Notice"

        msg = chat(
            "You write short, warm, one-line banking nudges. No emojis. Be specific.",
            f"Write a one-line nudge. Situation: {decision.insight.why}. Suggested action: {label}.",
        ) or decision.insight.why

        reasoning = list(s.evidence) + [
            f"Urgency {decision.insight.urgency:.2f} · expected value Rs{decision.insight.expected_value:,.0f}",
            f"Orchestrator: {decision.action.upper()} — {decision.reason}",
        ]
        return Nudge(title=title, message=msg, action_label=label, tool=tool,
                     tool_args=args, mode=s.mode, reasoning=reasoning,
                     regulated=regulated, reversible=True, journey=journey)
