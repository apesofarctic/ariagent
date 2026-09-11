from datetime import date, timedelta
from .schemas import Transaction


def generate(start: date | None = None) -> list[Transaction]:
    """60-day synthetic 'Priya' stream with planted signals:
    overdraft setup + duplicate sub (Protect), salary hike + roundup (Grow),
    baby pattern (Guide)."""
    start = start or date.today() - timedelta(days=60)
    txns: list[Transaction] = []
    for d in range(61):
        day = start + timedelta(days=d)
        # daily small spend (also feeds the low-value roundup signal)
        txns.append(Transaction(date=day, amount=-round(150 + (d % 5) * 40, 2),
                                merchant="Daily Spend", category="food"))
        # salary — hiked from day 30 onwards (Grow: salary_hike)
        if d == 0:
            txns.append(Transaction(date=day, amount=50000, merchant="ACME Payroll", category="salary"))
        if d in (30, 60):
            txns.append(Transaction(date=day, amount=57500, merchant="ACME Payroll", category="salary"))
        # rent
        if d in (28, 58):
            txns.append(Transaction(date=day, amount=-25000, merchant="Landlord", category="rent"))
        # planted DUPLICATE subscription (Protect)
        if d == 10:
            txns.append(Transaction(date=day, amount=-499, merchant="Netflix", category="subscription"))
        if d == 12:
            txns.append(Transaction(date=day, amount=-499, merchant="Netflix Premium", category="subscription"))
        # planted baby pattern (Guide: life_event_baby)
        if d == 44:
            txns.append(Transaction(date=day, amount=-850, merchant="Apollo Pharmacy", category="health"))
        if d == 48:
            txns.append(Transaction(date=day, amount=-2500, merchant="Motherhood Clinic", category="health"))
        if d == 52:
            txns.append(Transaction(date=day, amount=-1200, merchant="Apollo Pharmacy", category="health"))
        if d == 55:
            txns.append(Transaction(date=day, amount=-1999, merchant="FirstCry", category="shopping"))
    return txns
