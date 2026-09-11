import numpy as np
import pandas as pd
import pytest

from app.ml.population import generate_population
from app.ml.merchants import normalize_merchant
from app.categorize import categorize_by_rules
from app.ml.recurring import build_groups, classify_recurring, incumbent_duplicate_rule


@pytest.fixture(scope="module")
def small_pop():
    txns, custs = generate_population(n_customers=60, months=12, seed=11)
    txns["norm"] = txns["raw_merchant"].map(normalize_merchant)
    return txns, custs


def test_normalizer_collapses_raw_variants(small_pop):
    txns, _ = small_pop
    raw_variety = txns.groupby("true_merchant_canonical")["raw_merchant"].nunique().mean()
    norm_variety = txns.groupby("true_merchant_canonical")["norm"].nunique().mean()
    assert norm_variety < raw_variety / 5

    purity = txns.groupby("norm")["true_merchant_canonical"].apply(
        lambda s: s.value_counts(normalize=True).iloc[0])
    assert purity.mean() > 0.95


def test_rules_incumbent_runs_on_normalized_and_raw(small_pop):
    txns, _ = small_pop
    for col in ("raw_merchant", "norm"):
        preds = txns[col].map(lambda m: categorize_by_rules(m) or "other")
        assert set(preds.unique()) <= set(txns["true_category"].unique()) | {"other"}


def test_recurring_groups_and_classifier_shapes(small_pop):
    txns, _ = small_pop
    groups = build_groups(txns, key_col="norm")
    assert len(groups) > 0
    preds = classify_recurring(groups)
    assert preds.dtype == bool
    assert len(preds) == len(groups)


def test_incumbent_duplicate_rule_fires_more_on_raw_than_normalized(small_pop):
    txns, _ = small_pop
    raw_fired = incumbent_duplicate_rule(txns, "raw_merchant")["fired"].sum()
    norm_fired = incumbent_duplicate_rule(txns, "norm")["fired"].sum()
    # raw strings carry random reference numbers, so the naive "distinct
    # merchant string" check over-fires unless the input is normalised first
    assert raw_fired >= norm_fired
