from datetime import timedelta
from .base import Detector
from ..schemas import Signal

_BABY_HINTS = ("pharmacy", "clinic", "hospital", "motherhood", "maternity",
               "prenatal", "diagnostic", "pediatric", "firstcry")


class BabyLifeEventDetector(Detector):
    mode = "guide"

    def detect(self, txns, profile):
        if not txns:
            return []
        latest = max(t.date for t in txns)
        window = latest - timedelta(days=45)
        hits = [t for t in txns
                if t.date >= window and t.amount < 0
                and (t.category == "health"
                     or any(h in t.merchant.lower() for h in _BABY_HINTS))]
        if len(hits) < 3:
            return []
        merchants = sorted({t.merchant for t in hits})
        spend = round(sum(-t.amount for t in hits), 2)
        return [Signal(
            type="life_event_baby", mode="guide", confidence=0.7,
            evidence=[
                f"{len(hits)} health/maternity payments in the last 45 days "
                f"({', '.join(merchants[:4])})",
                f"Rs{spend:,.0f} of new health-related spend — a pattern that often "
                "means a growing family",
            ],
            data={"merchants": merchants, "count": len(hits), "spend": spend},
        )]
