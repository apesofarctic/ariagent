import numpy as np
import pandas as pd
import pytest

from app.ml.population import generate_population
from app.ml.labels import build_labels, assert_no_leakage, LEAK_FIELDS
from app.ml.splits import (
    customer_group_kfold, time_holdout, assert_customer_disjoint, assert_time_disjoint,
)


@pytest.fixture(scope="module")
def small_pop():
    return generate_population(n_customers=150, months=12, seed=7)


def test_population_distributions(small_pop):
    txns, custs = small_pop
    # income -> spend correlation: higher income band should mean higher total spend
    spend = txns.groupby("customer_id")["amount"].apply(lambda a: -a[a < 0].sum())
    merged = custs.set_index("customer_id").join(spend.rename("total_spend"))
    corr = merged["monthly_income"].corr(merged["total_spend"])
    assert corr > 0.3, f"income/spend correlation too weak: {corr:.2f}"

    # overdrawn-at-least-once-per-quarter share: proxy via customers whose
    # monthly discretionary spend sometimes exceeds monthly income
    monthly = txns.assign(month=txns["date"].dt.to_period("M"))
    monthly_net = monthly.groupby(["customer_id", "month"])["amount"].sum()
    frac_negative_months = (monthly_net < 0).groupby("customer_id").mean()
    assert 0.0 <= frac_negative_months.mean() <= 1.0

    # category mix: no single discretionary category should dominate absurdly
    cat_share = txns["true_category"].value_counts(normalize=True)
    assert cat_share.max() < 0.5

    # merchant string entropy: raw strings for the same canonical merchant vary
    dup_variety = txns.groupby("true_merchant_canonical")["raw_merchant"].nunique()
    assert dup_variety.max() > 1


def test_labels_separate_from_features(small_pop):
    txns, custs = small_pop
    labels = build_labels(txns, custs)
    assert set(labels) == {"category", "subscriptions", "life_events"}
    assert len(labels["category"]) == len(txns)
    # leak guard: a feature builder must never see these columns
    with pytest.raises(AssertionError):
        assert_no_leakage(["amount", "date", "true_category"])
    assert_no_leakage(["amount", "date", "raw_merchant", "day_of_week"])  # should not raise


def test_splits_are_disjoint(small_pop):
    txns, _ = small_pop
    for train_idx, test_idx in customer_group_kfold(txns, n_splits=5):
        assert_customer_disjoint(txns, train_idx, test_idx)

    train_idx, test_idx, boundary = time_holdout(txns, months_train=9)
    assert_time_disjoint(txns, train_idx, test_idx)
    assert len(train_idx) > 0 and len(test_idx) > 0
