"""Phase 0.2 — ground truth, kept separate from the feature path.

Because the population is generated, true category, true recurring
subscriptions and true life-event dates are all known exactly. They are
written to their own tables here, never merged back into anything a
model's feature builder touches — that separation is the leak guard.

Deferred: "true intervention responsiveness" (the fourth ground-truth
type the plan lists in §0.2) belongs to the phase-2 response simulator
(§2.1), which is out of scope for this phase-0/1 build. `population.py`
already carries the latent fields phase 2 will need (income_volatility,
digital_affinity) so it won't need to be regenerated when that lands.
"""
from __future__ import annotations

import pandas as pd

LEAK_FIELDS = {"true_category", "true_merchant_canonical", "is_subscription", "subscription_service"}


def build_labels(transactions: pd.DataFrame, customers_latent: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Returns the three label tables described in §0.2."""
    category_labels = transactions[["customer_id", "date", "raw_merchant", "true_category"]].copy()
    category_labels["txn_id"] = category_labels.index

    subs = transactions[transactions["is_subscription"]].copy()
    subs["txn_id"] = subs.index
    subscription_labels = subs[["txn_id", "customer_id", "date", "raw_merchant",
                                 "subscription_service"]].rename(
        columns={"subscription_service": "true_service"})

    life_event_labels = customers_latent.loc[
        customers_latent["has_baby_event"], ["customer_id", "baby_event_date"]
    ].rename(columns={"baby_event_date": "event_date"}).copy()
    life_event_labels["event_type"] = "baby"

    return {
        "category": category_labels,
        "subscriptions": subscription_labels,
        "life_events": life_event_labels,
    }


def assert_no_leakage(feature_columns: list[str]) -> None:
    """The leak guard: raise if any label field has snuck into a feature set."""
    leaked = LEAK_FIELDS & set(feature_columns)
    if leaked:
        raise AssertionError(f"label field(s) leaked into feature path: {leaked}")
