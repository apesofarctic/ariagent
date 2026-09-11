from datetime import timedelta
from .base import Detector
from ..schemas import Signal


class RoundupDetector(Detector):
    """Low-stakes 'spare change' opportunity — deliberately low urgency so the
    Orchestrator suppresses it. The restraint moment in the demo."""
    mode = "grow"

    def detect(self, txns, profile):
        if not txns:
            return []
        latest = max(t.date for t in txns)
        window = latest - timedelta(days=30)
        roundup = 0.0
        count = 0
        for t in txns:
            if t.date >= window and t.amount < 0:
                rem = (-t.amount) % 100
                if rem:
                    roundup += 100 - rem
                    count += 1
        if roundup < 100 or count < 5:
            return []
        return [Signal(
            type="roundup_potential", mode="grow", confidence=0.6,
            evidence=[f"Rounding up {count} everyday payments would have saved "
                      f"Rs{roundup:,.0f} this month"],
            data={"monthly": round(roundup, 2), "count": count},
        )]
