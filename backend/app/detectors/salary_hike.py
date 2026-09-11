from .base import Detector
from ..schemas import Signal


class SalaryHikeDetector(Detector):
    mode = "grow"

    def detect(self, txns, profile):
        credits = sorted((t for t in txns if t.category == "salary" and t.amount > 0),
                         key=lambda t: t.date)
        if len(credits) < 2:
            return []
        # most recent step-up of ≥10% between consecutive salary credits
        prev = latest = None
        for a, b in zip(credits, credits[1:]):
            if b.amount >= a.amount * 1.10:
                prev, latest = a, b
        if not latest:
            return []
        delta = round(latest.amount - prev.amount, 2)
        sip = int(round(delta * 0.4, -2)) or int(delta)  # suggest ~40% of the raise
        return [Signal(
            type="salary_hike", mode="grow", confidence=0.85,
            evidence=[
                f"Salary credit rose from Rs{prev.amount:,.0f} ({prev.date}) "
                f"to Rs{latest.amount:,.0f} ({latest.date})",
                f"That's Rs{delta:,.0f}/month of new recurring surplus",
            ],
            data={"old": prev.amount, "new": latest.amount,
                  "delta": delta, "sip_suggestion": sip},
        )]
