"""Phase 1.4 — recurring / duplicate-subscription detection.

Two related but distinct jobs, both keyed on (customer, normalized
merchant key) rather than raw strings:

1. Is this group a genuine recurring subscription? (inter-arrival
   regularity + amount stability + run length)
2. Do two DIFFERENT-looking merchant keys for the same customer actually
   belong to the same underlying service ("NETFLIX" vs "Netflix
   Premium")? Answered by embedding cosine similarity between the keys.
   Getting this merge right matters because an un-merged alias looks
   like two half-strength recurring series instead of one strong one.

The shipped incumbent (`duplicate_subscription.py`) answers a narrower
question — same rounded amount, >=2 distinct merchant strings — and,
critically, was written assuming clean merchant strings. Run directly on
the raw noisy statement strings this population generates, its distinct-
string check fires on almost every real subscription (every monthly
charge carries a different random reference number), which is why
merchants.py's normalisation has to run first for any of this to work.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

REGULARITY_CV_MAX = 0.35   # gap coefficient-of-variation threshold
AMOUNT_CV_MAX = 0.15       # amount coefficient-of-variation threshold
MIN_RUN_LENGTH = 3
DUPLICATE_SIM_THRESHOLD = 0.80


def build_groups(txns: pd.DataFrame, key_col: str = "norm") -> pd.DataFrame:
    """One row per (customer_id, key_col) group with regularity/stability features."""
    rows = []
    for (cust, key), g in txns.groupby(["customer_id", key_col]):
        g = g.sort_values("date")
        n = len(g)
        gaps = g["date"].diff().dropna().dt.days.to_numpy()
        amounts = g["amount"].abs().to_numpy()
        gap_cv = float(gaps.std() / gaps.mean()) if len(gaps) and gaps.mean() > 0 else np.inf
        amt_cv = float(amounts.std() / amounts.mean()) if amounts.mean() > 0 else np.inf
        true_is_sub = bool((g["true_category"] == "subscription").mean() > 0.5)
        rows.append(dict(
            customer_id=cust, key=key, n=n, gap_cv=gap_cv, amount_cv=amt_cv,
            run_length=n, true_is_subscription=true_is_sub,
        ))
    return pd.DataFrame(rows)


def classify_recurring(groups: pd.DataFrame) -> np.ndarray:
    """Threshold classifier on regularity + stability + run length."""
    return (
        (groups["n"] >= MIN_RUN_LENGTH)
        & (groups["gap_cv"] < REGULARITY_CV_MAX)
        & (groups["amount_cv"] < AMOUNT_CV_MAX)
    ).to_numpy()


def find_duplicate_pairs(groups: pd.DataFrame, embed_fn) -> pd.DataFrame:
    """For each customer's recurring keys, score every key pair by cosine
    similarity between embeddings of the (normalized) key strings.

    embed_fn: list[str] -> np.ndarray[n, d]. Returns a dataframe of pairwise
    predictions with customer_id, key_a, key_b, similarity, predicted_duplicate.
    """
    recurring = groups[classify_recurring(groups)]
    all_keys = sorted(recurring["key"].unique())
    if not all_keys:
        return pd.DataFrame(columns=["customer_id", "key_a", "key_b", "similarity", "predicted_duplicate"])
    vecs = embed_fn(all_keys)
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    key_to_vec = dict(zip(all_keys, vecs))

    rows = []
    for cust, g in recurring.groupby("customer_id"):
        keys = g["key"].tolist()
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = keys[i], keys[j]
                sim = float(np.dot(key_to_vec[a], key_to_vec[b]))
                rows.append(dict(customer_id=cust, key_a=a, key_b=b, similarity=sim,
                                  predicted_duplicate=sim > DUPLICATE_SIM_THRESHOLD))
    return pd.DataFrame(rows)


def incumbent_duplicate_rule(txns: pd.DataFrame, merchant_col: str) -> pd.DataFrame:
    """Reimplementation of app/detectors/duplicate_subscription.py's rule,
    parameterised by which merchant column to key on (raw vs normalized),
    so both can be scored on the same synthetic data.
    """
    subs = txns[txns["true_category"] == "subscription"]
    rows = []
    for cust, g in subs.groupby("customer_id"):
        by_amount: dict[int, set[str]] = {}
        for _, r in g.iterrows():
            amt = round(abs(r["amount"]))
            by_amount.setdefault(amt, set()).add(r[merchant_col])
        fired = any(len(ms) >= 2 for ms in by_amount.values())
        rows.append(dict(customer_id=cust, fired=fired))
    return pd.DataFrame(rows)
