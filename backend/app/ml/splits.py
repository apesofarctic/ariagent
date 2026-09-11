"""Phase 0.3 — customer-level GroupKFold + a time holdout.

Two different splits, for two different leaks:
- GroupKFold on customer_id stops the same customer appearing in both
  train and test within a fold (a customer's spending style is not iid
  across their own transactions).
- The time holdout (fit months 1-9, evaluate months 10-12) stops a
  backward-looking feature from ever seeing its own future.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold


def customer_group_kfold(transactions: pd.DataFrame, n_splits: int = 5, seed: int = 42):
    """Yields (train_idx, test_idx) over `transactions`' row index, grouped by customer_id."""
    gkf = GroupKFold(n_splits=n_splits)
    customer_ids = transactions["customer_id"].to_numpy()
    # GroupKFold has no shuffle/seed; shuffle customer order beforehand instead.
    rng = np.random.default_rng(seed)
    unique_customers = transactions["customer_id"].unique()
    order = rng.permutation(unique_customers)
    rank = {c: i for i, c in enumerate(order)}
    shuffled_groups = np.array([rank[c] for c in customer_ids])
    idx = np.arange(len(transactions))
    for train_idx, test_idx in gkf.split(idx, groups=shuffled_groups):
        yield train_idx, test_idx


def time_holdout(transactions: pd.DataFrame, months_train: int = 9):
    """Fit on months 1..months_train, evaluate on the remainder.

    Assumes population.py's convention of 30-day months from a fixed start date.
    """
    start = transactions["date"].min()
    boundary = start + pd.Timedelta(days=months_train * 30)
    train_mask = transactions["date"] < boundary
    test_mask = ~train_mask
    return transactions.index[train_mask], transactions.index[test_mask], boundary


def assert_customer_disjoint(transactions: pd.DataFrame, train_idx, test_idx) -> None:
    train_customers = set(transactions.loc[train_idx, "customer_id"])
    test_customers = set(transactions.loc[test_idx, "customer_id"])
    overlap = train_customers & test_customers
    assert not overlap, f"{len(overlap)} customers leak across the fold boundary"


def assert_time_disjoint(transactions: pd.DataFrame, train_idx, test_idx) -> None:
    train_max = transactions.loc[train_idx, "date"].max()
    test_min = transactions.loc[test_idx, "date"].min()
    assert train_max < test_min, f"train max {train_max} >= test min {test_min}"
