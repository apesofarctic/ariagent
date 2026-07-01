from ..detectors.overdraft import OverdraftDetector
from ..detectors.duplicate_subscription import DuplicateSubscriptionDetector


class Sentinel:
    def __init__(self):
        self.detectors = [OverdraftDetector(), DuplicateSubscriptionDetector()]

    def sense(self, txns, profile):
        signals = []
        for d in self.detectors:
            signals.extend(d.detect(txns, profile))
        return signals
