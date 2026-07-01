from datetime import date, timedelta
from .schemas import Transaction


def generate(start: date | None = None) -> list[Transaction]:
    """60-day synthetic stream with planted signals (salary, rent, duplicate sub)."""
    start = start or date.today() - timedelta(days=60)
    txns: list[Transaction] = []
    for d in range(61):
        day = start + timedelta(days=d)
        # daily small spend
        txns.append(Transaction(date=day, amount=-round(150 + (d % 5) * 40, 2),
                                merchant="Daily Spend", category="food"))
        # salary
        if d in (0, 30, 60):
            txns.append(Transaction(date=day, amount=50000, merchant="ACME Payroll", category="salary"))
        # rent
        if d in (28, 58):
            txns.append(Transaction(date=day, amount=-25000, merchant="Landlord", category="rent"))
        # planted DUPLICATE subscription
        if d == 10:
            txns.append(Transaction(date=day, amount=-499, merchant="Netflix", category="subscription"))
        if d == 12:
            txns.append(Transaction(date=day, amount=-499, merchant="Netflix Premium", category="subscription"))
    return txns
