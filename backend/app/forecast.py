"""Deterministic cashflow forecast for the dashboard chart.

Correctness-critical money math stays in plain Python — never the LLM.
"""
from datetime import date, timedelta

from .schemas import Transaction


def forecast_balance(txns: list[Transaction], profile: dict, days: int = 35) -> dict:
    today = max((t.date for t in txns), default=date.today())
    balance = float(profile.get("current_balance", 0.0))

    # average daily discretionary spend over the trailing 30 days
    window = today - timedelta(days=30)
    recurring_cats = {"salary", "rent"}
    spend = [-t.amount for t in txns
             if t.date >= window and t.amount < 0 and t.category not in recurring_cats]
    daily_spend = round(sum(spend) / 30.0, 2) if spend else 0.0

    recurring = profile.get("recurring", [])
    points = [{"date": str(today), "balance": round(balance, 2)}]
    running = balance
    for i in range(1, days + 1):
        day = today + timedelta(days=i)
        running -= daily_spend
        for r in recurring:
            if day.day == r["day_of_month"]:
                running += r["amount"] if r["type"] == "salary" else -abs(r["amount"])
        points.append({"date": str(day), "balance": round(running, 2)})

    low = min(p["balance"] for p in points)
    return {
        "points": points,
        "daily_spend": daily_spend,
        "min_balance": low,
        "overdraft_risk": low < 0,
        "buffer": 2000.0,   # "getting close" threshold for the amber band
    }
