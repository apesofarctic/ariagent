from collections import defaultdict
from .base import Detector
from ..schemas import Signal


class DuplicateSubscriptionDetector(Detector):
    mode = "protect"

    def detect(self, txns, profile):
        subs = [t for t in txns if t.category == "subscription"]
        by_amount = defaultdict(list)
        for t in subs:
            by_amount[round(abs(t.amount))].append(t)
        signals = []
        for amount, items in by_amount.items():
            if len(items) >= 2:
                merchants = sorted({t.merchant for t in items})
                signals.append(Signal(
                    type="duplicate_subscription", mode="protect", confidence=0.8,
                    evidence=[f"{len(items)} charges of Rs{amount} ({', '.join(merchants)})"],
                    data={"amount": amount, "merchants": merchants},
                ))
        return signals
