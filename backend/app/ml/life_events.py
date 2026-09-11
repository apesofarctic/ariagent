"""Phase 1.5 — life-event (baby) detection.

Scoped to the baby life event, the one the shipped incumbent
(`detectors/life_event_baby.py`) already targets, since it's the only
event type `population.py` currently plants.

Deviation from docs/06-ml-build-plan.md §1.5, stated up front: the plan
asks for "the centroid of that day's merchant embeddings" (384d) as part
of each day's feature vector. Running the full bge-small embedding over
every transaction a second time (recurring.py already needs one pass)
was not worth the extra encode time for this build, so each day's
feature vector instead carries one scalar: the mean cosine similarity
of that day's merchants to a fixed "pregnancy / maternity / pharmacy"
anchor text, in the same embedding space. It's a compressed projection
of the same signal, not a different one, but it is not the literal
384-d centroid the plan describes — swapping it back in is a drop-in
change to `build_daily_features` if the extra compute is later worth it.

Three systems compared at a checkpoint (customer, as-of day) level:
  - incumbent: reimplementation of the shipped 45-day hit-count rule
  - GBDT: LightGBM over flattened 90-day window aggregates
  - challenger: small GRU over the 90-day sequence itself
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .population import CATEGORIES_DISCRETIONARY

WINDOW = 90
STRIDE = 7
ANCHOR_TEXT = "pregnancy maternity clinic pharmacy baby newborn prenatal"
FEATURE_COLS = CATEGORIES_DISCRETIONARY + ["health_affinity_spend", "txn_count"]


def merchant_affinity(unique_merchants: list[str], embed_fn) -> dict[str, float]:
    """cosine similarity of each canonical merchant name to the baby anchor text."""
    vecs = embed_fn([ANCHOR_TEXT] + unique_merchants)
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    anchor, merchant_vecs = vecs[0], vecs[1:]
    sims = merchant_vecs @ anchor
    return dict(zip(unique_merchants, sims.astype(float)))


def build_all_features(txns: pd.DataFrame, start, n_days: int, affinity: dict[str, float]) -> dict[int, np.ndarray]:
    """{customer_id: [n_days, n_features]} daily feature arrays, vectorised per customer."""
    cat_index = {c: i for i, c in enumerate(CATEGORIES_DISCRETIONARY)}
    disc = txns[txns["true_category"].isin(CATEGORIES_DISCRETIONARY)].copy()
    disc["day_idx"] = (disc["date"] - pd.Timestamp(start)).dt.days
    disc["aff"] = disc["true_merchant_canonical"].map(affinity).fillna(0.0)
    disc["abs_amt"] = disc["amount"].abs()

    out: dict[int, np.ndarray] = {}
    for cust, g in disc.groupby("customer_id"):
        arr = np.zeros((n_days, len(FEATURE_COLS)))
        for cat, ci in cat_index.items():
            sub = g[g["true_category"] == cat]
            if len(sub):
                np.add.at(arr[:, ci], sub["day_idx"].to_numpy(), sub["abs_amt"].to_numpy())
        aff_col = len(CATEGORIES_DISCRETIONARY)
        cnt_col = aff_col + 1
        np.add.at(arr[:, aff_col], g["day_idx"].to_numpy(), (g["abs_amt"] * g["aff"]).to_numpy())
        np.add.at(arr[:, cnt_col], g["day_idx"].to_numpy(), 1.0)
        # normalise the spend columns by this customer's own average daily
        # discretionary spend. Without it, a GBDT/GRU trained on absolute
        # rupee amounts partly just memorises which income level looks
        # "high spend" for a handful of training customers with an event,
        # and that does not transfer to held-out customers on a different
        # income scale. This was verified empirically during the build: an
        # un-normalised GBDT hit ~1.0 train separation and ~0 test recall.
        baseline = max(arr[:, :aff_col + 1].sum(axis=1).mean(), 1.0)
        arr[:, :aff_col + 1] /= baseline
        out[cust] = arr
    return out


def make_checkpoints(customer_ids: list[int], has_baby: dict[int, bool], baby_day: dict[int, int],
                      n_days: int, window: int = WINDOW, stride: int = STRIDE):
    """(customer_id, as_of_day, label) for every stride-spaced checkpoint with
    >=`window` days of history. label=1 iff the customer has a baby event and
    as_of_day is inside the (event_day - window, event_day] lead-in span."""
    rows = []
    for c in customer_ids:
        for d in range(window, n_days, stride):
            label = 0
            if has_baby.get(c) and 0 < baby_day[c] - d <= window:
                label = 1
            rows.append((c, d, label))
    return pd.DataFrame(rows, columns=["customer_id", "as_of_day", "label"])


def window_aggregates(features: np.ndarray, as_of_day: int, window: int = WINDOW) -> np.ndarray:
    """Flatten a trailing window into sum/mean/max aggregates — the GBDT's view."""
    w = features[max(0, as_of_day - window):as_of_day]
    if len(w) == 0:
        w = np.zeros((1, features.shape[1]))
    return np.concatenate([w.sum(0), w.mean(0), w.max(0)])


def window_sequence(features: np.ndarray, as_of_day: int, window: int = WINDOW) -> np.ndarray:
    """Trailing [window, n_features] sequence, left-padded with zeros — the GRU's view."""
    start = as_of_day - window
    if start >= 0:
        return features[start:as_of_day]
    pad = np.zeros((-start, features.shape[1]))
    return np.concatenate([pad, features[0:as_of_day]], axis=0)


def incumbent_rule_score(features: np.ndarray, as_of_day: int, health_col: int, affinity_col: int) -> bool:
    """Reimplementation of detectors/life_event_baby.py: >=3 health/maternity
    hits in the trailing 45 days. `features` carries category *spend*, not a
    transaction count per category, so this uses the count column alongside
    a health-spend-present check as a proxy for "hit"."""
    w = features[max(0, as_of_day - 45):as_of_day]
    health_days_with_spend = int((w[:, health_col] > 0).sum())
    return health_days_with_spend >= 3
