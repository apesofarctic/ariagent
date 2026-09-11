from ..schemas import Signal, Insight
from ..llm import chat

URGENCY = {
    "overdraft_forecast": 0.9,
    "duplicate_subscription": 0.4,
    "salary_hike": 0.55,
    "life_event_baby": 0.65,
    "roundup_potential": 0.2,   # deliberately below the fire threshold → suppressed
}


class InsightAgent:
    def reason(self, signal: Signal, profile: dict) -> Insight:
        urgency = URGENCY.get(signal.type, 0.5) * signal.confidence
        if signal.type == "overdraft_forecast":
            ev = signal.data.get("shortfall", 0) * 0.3      # proxy: avoided NSF cost
        elif signal.type == "duplicate_subscription":
            ev = signal.data.get("amount", 0) * 12          # annual saving
        elif signal.type == "salary_hike":
            ev = signal.data.get("delta", 0) * 12           # annual new surplus
        elif signal.type == "life_event_baby":
            ev = 5000.0                                     # proxy: value of planning early
        elif signal.type == "roundup_potential":
            ev = signal.data.get("monthly", 0) * 12
        else:
            ev = 0.0
        return Insight(signal=signal, urgency=round(urgency, 2),
                       expected_value=round(ev, 2), why=self._explain(signal))

    def _explain(self, signal: Signal) -> str:
        out = chat(
            "You are a concise financial reasoning assistant. One plain-language sentence. No advice yet.",
            f"Explain why this matters to the customer: {signal.type}. Evidence: {signal.evidence}.",
        )
        return out or "; ".join(signal.evidence)   # deterministic fallback
