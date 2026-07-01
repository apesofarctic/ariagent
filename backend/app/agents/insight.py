from ..schemas import Signal, Insight
from ..llm import chat

URGENCY = {"overdraft_forecast": 0.9, "duplicate_subscription": 0.4}


class InsightAgent:
    def reason(self, signal: Signal, profile: dict) -> Insight:
        urgency = URGENCY.get(signal.type, 0.5) * signal.confidence
        if signal.type == "overdraft_forecast":
            ev = signal.data.get("shortfall", 0) * 0.3      # proxy: avoided NSF cost
        elif signal.type == "duplicate_subscription":
            ev = signal.data.get("amount", 0) * 12          # annual saving
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
