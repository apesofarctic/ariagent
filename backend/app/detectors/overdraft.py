from datetime import date
from .base import Detector
from ..schemas import Signal
from ..utils import next_day_of_month


class OverdraftDetector(Detector):
    mode = "protect"

    def detect(self, txns, profile):
        signals = []
        bal = profile["current_balance"]
        recurring = {r["type"]: r for r in profile.get("recurring", [])}
        if "rent" in recurring and "salary" in recurring:
            today = max((t.date for t in txns), default=date.today())
            rent, salary = recurring["rent"], recurring["salary"]
            rent_date = next_day_of_month(today, rent["day_of_month"])
            salary_date = next_day_of_month(today, salary["day_of_month"])
            if rent_date < salary_date and bal < rent["amount"]:
                signals.append(Signal(
                    type="overdraft_forecast", mode="protect", confidence=0.95,
                    evidence=[
                        f"Balance Rs{bal:.0f} is below upcoming rent Rs{rent['amount']:.0f}",
                        f"Rent debits {rent_date}, but salary only lands {salary_date}",
                    ],
                    data={"shortfall": round(rent["amount"] - bal, 2),
                          "rent_date": str(rent_date), "salary_date": str(salary_date),
                          "rent_amount": rent["amount"]},
                ))
        return signals
