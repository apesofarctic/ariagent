"""Phase 1.1 + 1.3 — categorizer bake-off.

Incumbent (shipped rules table) vs. rules+normalizer vs. the embedding
challenger, scored on the same held-out customers (customer-level
GroupKFold, see app/ml/splits.py). Writes evals/report_categorizer.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder

from app.categorize import categorize_by_rules, CATEGORIES
from app.ml.merchants import normalize_merchant
from app.ml.population import generate_population
from app.ml.splits import customer_group_kfold

KEY_CLASSES = ["subscription", "salary", "rent", "health"]
N_BOOTSTRAP = 500


def score_rules(raw_merchants, true_categories, normalize: bool) -> dict:
    preds = []
    for m in raw_merchants:
        target = normalize_merchant(m) if normalize else m
        cat = categorize_by_rules(target)
        preds.append(cat or "other")
    preds = np.array(preds)
    return _metrics(true_categories, preds)


def _metrics(y_true, y_pred) -> dict:
    labels = sorted(set(y_true) | set(y_pred))
    macro_f1 = f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    coverage = float(np.mean(np.array(y_pred) != "other"))
    per_class_recall = {}
    for c in KEY_CLASSES:
        if c in labels:
            per_class_recall[c] = float(recall_score(
                y_true, y_pred, labels=[c], average="micro", zero_division=0))
    return {"macro_f1": float(macro_f1), "coverage": coverage, "per_class_recall": per_class_recall}


def bootstrap_margin_ci(y_true, pred_a, pred_b, n_boot=N_BOOTSTRAP, seed=0) -> dict:
    """CI on macro-F1(pred_b) - macro-F1(pred_a), resampling held-out rows."""
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    pred_a = np.asarray(pred_a)
    pred_b = np.asarray(pred_b)
    n = len(y_true)
    labels = sorted(set(y_true) | set(pred_a) | set(pred_b))
    margins = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        f1_a = f1_score(y_true[idx], pred_a[idx], labels=labels, average="macro", zero_division=0)
        f1_b = f1_score(y_true[idx], pred_b[idx], labels=labels, average="macro", zero_division=0)
        margins[i] = f1_b - f1_a
    lo, hi = np.percentile(margins, [2.5, 97.5])
    return {"margin_mean": float(margins.mean()), "ci_low": float(lo), "ci_high": float(hi),
             "clears_ci": bool(lo > 0)}


def run(n_customers: int = 3000, months: int = 12, seed: int = 42) -> dict:
    t0 = time.time()
    txns, custs = generate_population(n_customers=n_customers, months=months, seed=seed)
    print(f"population: {len(txns):,} rows, {len(custs):,} customers ({time.time()-t0:.1f}s)")

    # one held-out fold, customer-disjoint, for the whole bake-off
    train_idx, test_idx = next(customer_group_kfold(txns, n_splits=5, seed=seed))
    train, test = txns.loc[train_idx], txns.loc[test_idx]
    print(f"train {len(train):,} / test {len(test):,} rows "
          f"({train.customer_id.nunique()} / {test.customer_id.nunique()} customers)")

    y_test = test["true_category"].to_numpy()

    # 1.1 incumbent: raw rules
    raw_rules_preds = np.array([categorize_by_rules(m) or "other" for m in test["raw_merchant"]])
    m_raw = _metrics(y_test, raw_rules_preds)

    # 1.2 rules + normalizer
    norm_rules_preds = np.array([
        categorize_by_rules(normalize_merchant(m)) or "other" for m in test["raw_merchant"]
    ])
    m_norm = _metrics(y_test, norm_rules_preds)

    # 1.3 challenger: embedding classifier
    from app.ml.categorizer import EmbeddingCategorizer
    t1 = time.time()
    clf = EmbeddingCategorizer().fit(train["raw_merchant"], train["true_category"])
    challenger_preds = clf.predict(test["raw_merchant"])
    print(f"embedding classifier fit+predict: {time.time()-t1:.1f}s")
    m_challenger = _metrics(y_test, challenger_preds)

    ci_vs_raw = bootstrap_margin_ci(y_test, raw_rules_preds, challenger_preds)
    ci_vs_norm = bootstrap_margin_ci(y_test, norm_rules_preds, challenger_preds)

    keep_or_drop = "keep challenger" if ci_vs_norm["clears_ci"] else "drop challenger, rules stay"

    report = {
        "n_customers": n_customers, "months": months,
        "train_rows": len(train), "test_rows": len(test),
        "1.1_rules_raw": m_raw,
        "1.2_rules_normalized": m_norm,
        "1.3_embedding_challenger": m_challenger,
        "margin_challenger_vs_raw_rules": ci_vs_raw,
        "margin_challenger_vs_normalized_rules": ci_vs_norm,
        "keep_or_drop": keep_or_drop,
        "runtime_s": round(time.time() - t0, 1),
    }
    out_path = Path(__file__).parent / "report_categorizer.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
