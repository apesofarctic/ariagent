"""Phase 0.1 — synthetic population generator.

Generates N synthetic retail customers over `months` months of daily
transactions. Each customer carries latent attributes that are NEVER
exposed to any model: income band, payroll employer and salary day, rent
day/amount, per-category spend propensity, digital-channel affinity,
income volatility, and (for a subset) a life-event schedule.

Deviation from docs/06-ml-build-plan.md §0.1, stated up front: the plan
specifies 12,000 customers. This build defaults to N_CUSTOMERS=3000 to
keep the full phase-0/1 sweep (population -> embeddings -> GRU training)
inside a single build session's compute budget. The generator itself is
parameterised, so re-running at n_customers=12000 is a one-line change
when the extra scale is worth the extra runtime; nothing else in phase 0
or phase 1 depends on the literal 12,000 figure.

Merchant strings are emitted the way a real statement carries them: a
payment-rail prefix, a reference number, occasional truncation, and a
city suffix. That mess is exactly what merchants.py / categorizer.py have
to cope with.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date, timedelta

CATEGORIES_DISCRETIONARY = [
    "food", "groceries", "transport", "shopping", "utilities", "health",
    "entertainment", "emi", "insurance", "investment", "transfer", "cash",
    "education", "travel",
]

# canonical merchant -> category, for discretionary spend. Names deliberately
# overlap with backend/app/categorize.py's RULES keywords so the rules
# incumbent gets a fair shot at them.
MERCHANT_POOL: dict[str, list[str]] = {
    "food": ["Swiggy", "Zomato", "Dominos", "McDonalds", "Starbucks", "Cafe Coffee Day", "EatSure"],
    "groceries": ["BigBasket", "Blinkit", "Zepto", "Instamart", "DMart", "More Supermarket"],
    "transport": ["Uber", "Ola", "Rapido", "IRCTC", "Metro", "HPCL Petrol"],
    "shopping": ["Amazon", "Flipkart", "Myntra", "Ajio", "Nykaa", "Meesho", "Decathlon"],
    "utilities": ["Airtel", "Jio", "BESCOM Electricity", "Tata Power", "ACT Fibernet"],
    "health": ["Apollo Pharmacy", "PharmEasy", "1mg", "Practo Clinic", "Netmeds"],
    "entertainment": ["BookMyShow", "PVR Cinemas", "INOX", "Steam"],
    "emi": ["Bajaj Finserv EMI", "Home Credit EMI"],
    "insurance": ["LIC Policy", "Star Health Insurance", "Acko Insurance"],
    "investment": ["Zerodha SIP", "Groww Mutual Fund", "Kuvera SIP"],
    "transfer": ["UPI Transfer Friend", "IMPS Transfer Family"],
    "cash": ["ATM Cash Wdl"],
    "education": ["Udemy", "Coursera", "Byjus Tuition"],
    "travel": ["MakeMyTrip", "OYO Rooms", "IndiGo Airlines"],
}

# baby-life-event elevated categories, used only for the affected 90-day window
BABY_MERCHANTS = {
    "health": ["Apollo Pharmacy", "Motherhood Clinic", "Cloudnine Hospital"],
    "shopping": ["FirstCry", "Amazon"],
}

SUBSCRIPTIONS = {
    # canonical service -> (monthly amount, aliases used to build near-duplicate raw strings)
    "Netflix": (499, ["Netflix", "Netflix Premium"]),
    "Spotify": (119, ["Spotify", "Spotify Premium"]),
    "Hotstar": (299, ["Hotstar", "Disney Hotstar"]),
    "Prime Video": (179, ["Prime Video", "Amazon Prime Video"]),
    "YouTube Premium": (129, ["YouTube Premium", "YouTube"]),
    "Audible": (199, ["Audible", "Audible Membership"]),
}

PAYROLL_EMPLOYERS = [
    "Acme Corp", "Globex Ltd", "Initech", "Umbrella Retail", "Stark Industries",
    "Wayne Enterprises", "Wonka Foods", "Hooli Tech", "Vandelay Industries", "Soylent Co",
]

CITY_SUFFIX = ["BLR", "MUM", "DEL", "HYD", "PUN", "CHN", "KOL"]
RAIL_PREFIX = ["UPI-", "POS ", "NEFT-CR-", "IMPS/", ""]


def _format_raw_merchant(rng: np.random.Generator, canonical: str, allow_truncation: bool = True) -> str:
    """Mangle a canonical merchant name into a realistic statement string.

    allow_truncation=False for subscription aliases: truncation noise would
    otherwise fragment a single alias into several normalized keys just as
    often as genuine alias switching does, which drowns the near-duplicate
    (alias-switching) signal that recurring.py's 1.4 eval is meant to probe.
    """
    name = canonical.upper().replace(" ", "")
    prefix = rng.choice(RAIL_PREFIX, p=[0.30, 0.25, 0.15, 0.15, 0.15])
    ref = "".join(str(d) for d in rng.integers(0, 10, size=int(rng.integers(6, 13))))
    city = rng.choice(CITY_SUFFIX)
    if allow_truncation and rng.random() < 0.25 and len(name) > 5:  # statement truncation
        name = name[: int(rng.integers(5, len(name) + 1))]
    return f"{prefix}{name}{ref}{city}"


def generate_population(
    n_customers: int = 3000,
    months: int = 12,
    start: date | None = None,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (transactions, customers_latent).

    transactions columns: customer_id, date, amount, raw_merchant,
        true_category, true_merchant_canonical, is_subscription,
        subscription_service (canonical service name or None).
    customers_latent columns: customer_id, income_band, monthly_income,
        payroll_employer, salary_day, is_renter, rent_day, rent_amount,
        digital_affinity, income_volatility, has_baby_event, baby_event_date.
    """
    rng = np.random.default_rng(seed)
    start = start or date(2025, 1, 1)
    n_days = months * 30
    days = [start + timedelta(days=d) for d in range(n_days)]

    income_bands = rng.choice(["low", "mid", "high"], size=n_customers, p=[0.4, 0.45, 0.15])
    band_mean = {"low": 28000, "mid": 55000, "high": 110000}
    monthly_income = np.array([
        rng.lognormal(mean=np.log(band_mean[b]), sigma=0.18) for b in income_bands
    ])
    payroll_employer = rng.choice(PAYROLL_EMPLOYERS, size=n_customers)
    salary_day = rng.integers(1, 29, size=n_customers)
    is_renter = rng.random(n_customers) < 0.55
    rent_day = rng.integers(1, 10, size=n_customers)
    rent_amount = monthly_income * rng.uniform(0.18, 0.35, size=n_customers)
    digital_affinity = rng.uniform(0.3, 0.95, size=n_customers)
    income_volatility = rng.uniform(0.01, 0.12, size=n_customers)

    # per-category daily spend propensity: Dirichlet weights * an overall daily rate
    n_cat = len(CATEGORIES_DISCRETIONARY)
    cat_weights = rng.dirichlet(np.ones(n_cat) * 1.5, size=n_customers)
    overall_daily_rate = rng.uniform(0.6, 1.6, size=n_customers)  # expected discretionary txns/day

    # subscriptions: each customer subscribes to 0-3 services independently
    sub_names = list(SUBSCRIPTIONS.keys())
    sub_matrix = rng.random((n_customers, len(sub_names))) < 0.22

    # 8% of customers get a baby life event, timed so there's a 90-day lead-in
    # window and at least 30 days of runway left in the horizon
    has_baby = rng.random(n_customers) < 0.08
    baby_day_idx = rng.integers(100, n_days - 30, size=n_customers)

    customers_latent = pd.DataFrame({
        "customer_id": np.arange(n_customers),
        "income_band": income_bands,
        "monthly_income": monthly_income,
        "payroll_employer": payroll_employer,
        "salary_day": salary_day,
        "is_renter": is_renter,
        "rent_day": rent_day,
        "rent_amount": rent_amount,
        "digital_affinity": digital_affinity,
        "income_volatility": income_volatility,
        "has_baby_event": has_baby,
        "baby_event_date": [days[i] if has_baby[c] else None for c, i in enumerate(baby_day_idx)],
    })

    rows: list[dict] = []
    for c in range(n_customers):
        c_rng = np.random.default_rng(seed * 1_000_003 + c)
        income = monthly_income[c]
        vol = income_volatility[c]

        # salary — once a month on salary_day, with small noise
        for m in range(months):
            day_idx = m * 30 + (salary_day[c] - 1)
            if day_idx >= n_days:
                continue
            amt = income * (1 + c_rng.normal(0, vol))
            # real salary narrations usually (not always) carry the word
            # SALARY alongside the employer name — the rules incumbent's
            # "salary"/"payroll" keywords depend on it being there
            payee = f"Salary {payroll_employer[c]}" if c_rng.random() < 0.7 else payroll_employer[c]
            rows.append(dict(
                customer_id=c, date=days[day_idx], amount=round(amt, 2),
                raw_merchant=_format_raw_merchant(c_rng, payee),
                true_category="salary", true_merchant_canonical=payroll_employer[c],
                is_subscription=False, subscription_service=None,
            ))

        # rent — once a month, if renter
        if is_renter[c]:
            for m in range(months):
                day_idx = m * 30 + (rent_day[c] - 1)
                if day_idx >= n_days:
                    continue
                rows.append(dict(
                    customer_id=c, date=days[day_idx], amount=-round(rent_amount[c], 2),
                    raw_merchant=_format_raw_merchant(c_rng, "Landlord"),
                    true_category="rent", true_merchant_canonical="Landlord",
                    is_subscription=False, subscription_service=None,
                ))

        # subscriptions — monthly cadence, +/- 2 day jitter, near-duplicate
        # raw strings for the same canonical service on purpose
        for si, sub in enumerate(sub_names):
            if not sub_matrix[c, si]:
                continue
            amount, aliases = SUBSCRIPTIONS[sub]
            anchor_day = int(c_rng.integers(1, 28))
            # a customer's statement text for one subscription is normally
            # stable — pick one alias for the year. A minority (~15%) of
            # subscribers switch alias partway through (a plan upgrade, a
            # billing-name change), which is the genuine near-duplicate case
            # 1.4's embedding-similarity merge step is meant to catch.
            primary_alias = c_rng.choice(aliases)
            other_alias = next((a for a in aliases if a != primary_alias), primary_alias)
            switches_alias = len(aliases) > 1 and c_rng.random() < 0.15
            switch_month = int(c_rng.integers(2, months)) if switches_alias else months
            for m in range(months):
                day_idx = m * 30 + anchor_day - 1 + int(c_rng.integers(-2, 3))
                if not (0 <= day_idx < n_days):
                    continue
                alias = other_alias if m >= switch_month else primary_alias
                rows.append(dict(
                    customer_id=c, date=days[day_idx], amount=-float(amount),
                    raw_merchant=_format_raw_merchant(c_rng, alias, allow_truncation=False),
                    true_category="subscription", true_merchant_canonical=sub,
                    is_subscription=True, subscription_service=sub,
                ))

        # discretionary spend, day by day
        rate = overall_daily_rate[c]
        weights = cat_weights[c]
        n_txn_per_day = c_rng.poisson(rate, size=n_days)
        for d, k in enumerate(n_txn_per_day):
            if k == 0:
                continue
            cats = c_rng.choice(CATEGORIES_DISCRETIONARY, size=k, p=weights)
            in_baby_window = (
                has_baby[c] and baby_day_idx[c] - 90 <= d < baby_day_idx[c]
            )
            for cat in cats:
                if in_baby_window and cat in BABY_MERCHANTS and c_rng.random() < 0.6:
                    pool = BABY_MERCHANTS[cat]
                    base_amt = {"health": 900, "shopping": 1500}[cat]
                else:
                    pool = MERCHANT_POOL[cat]
                    base_amt = {"food": 250, "groceries": 900, "transport": 180,
                                "shopping": 1200, "utilities": 600, "health": 500,
                                "entertainment": 400, "emi": 3500, "insurance": 2000,
                                "investment": 5000, "transfer": 800, "cash": 2000,
                                "education": 700, "travel": 3000}[cat]
                merchant = c_rng.choice(pool)
                amt = base_amt * (0.4 + income / 55000 * 0.6) * c_rng.lognormal(0, 0.35)
                rows.append(dict(
                    customer_id=c, date=days[d], amount=-round(float(amt), 2),
                    raw_merchant=_format_raw_merchant(c_rng, merchant),
                    true_category=cat, true_merchant_canonical=merchant,
                    is_subscription=False, subscription_service=None,
                ))

    transactions = pd.DataFrame(rows)
    transactions["date"] = pd.to_datetime(transactions["date"])
    return transactions, customers_latent


if __name__ == "__main__":
    import time
    t0 = time.time()
    txns, custs = generate_population()
    print(f"generated {len(txns):,} transactions for {len(custs):,} customers in {time.time()-t0:.1f}s")
    print(txns.head())
    print(txns["true_category"].value_counts())
