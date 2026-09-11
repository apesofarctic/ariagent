from ..detectors.overdraft import OverdraftDetector
from ..detectors.duplicate_subscription import DuplicateSubscriptionDetector
from ..detectors.salary_hike import SalaryHikeDetector
from ..detectors.life_event_baby import BabyLifeEventDetector
from ..detectors.roundup import RoundupDetector


class Sentinel:
    def __init__(self):
        self.detectors = [
            OverdraftDetector(), DuplicateSubscriptionDetector(),   # protect
            SalaryHikeDetector(), RoundupDetector(),                # grow
            BabyLifeEventDetector(),                                # guide
        ]

    def sense(self, txns, profile, consented_modes: set[str] | None = None,
              skip_types: set[str] | None = None):
        signals = []
        for d in self.detectors:
            if consented_modes is not None and d.mode not in consented_modes:
                continue
            signals.extend(d.detect(txns, profile))
        if skip_types:  # inference types the user marked "this is wrong"
            signals = [s for s in signals if s.type not in skip_types]
        return signals
