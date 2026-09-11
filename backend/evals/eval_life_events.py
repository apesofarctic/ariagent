"""Phase 1.5 — life-event (baby) detection: incumbent rule vs GBDT vs GRU.

Checkpoint-level task: for each (customer, as-of day) with >=90 days of
history, predict whether that customer is currently inside the 90-day
lead-in to a baby event. Metrics: precision/recall at a fixed operating
point, plus lead time in days (event_day - first day the customer's
checkpoints turn positive), which is the metric the plan calls out as
the one that actually matters.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import GroupKFold


def _best_f1_threshold(y_true, proba) -> float:
    """Operating point calibrated on the set passed in (train), not test —
    same discipline the plan applies to the grounding gate's threshold."""
    candidates = np.unique(proba)
    if len(candidates) > 200:
        candidates = np.quantile(candidates, np.linspace(0, 1, 200))
    best_t, best_f1 = 0.5, -1.0
    for t in candidates:
        f1 = f1_score(y_true, proba >= t, zero_division=0)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return float(best_t)

from app.ml.life_events import (
    FEATURE_COLS, WINDOW, STRIDE, build_all_features, make_checkpoints,
    merchant_affinity, window_aggregates, window_sequence, incumbent_rule_score,
)

HEALTH_COL = FEATURE_COLS.index("health")
AFFINITY_COL = FEATURE_COLS.index("health_affinity_spend")


def _embed_fn(texts):
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", threads=8)
    return np.array(list(model.embed(list(texts), batch_size=64)))


def lead_time_days(scores_by_customer: dict[int, np.ndarray], as_of_days: dict[int, np.ndarray],
                    baby_day: dict[int, int], threshold: float) -> dict:
    leads = []
    detected = 0
    total_positive_customers = 0
    for c, event_day in baby_day.items():
        total_positive_customers += 1
        days = as_of_days[c]
        scores = scores_by_customer[c]
        in_window = (days > event_day - WINDOW) & (days <= event_day)
        cand_days, cand_scores = days[in_window], scores[in_window]
        fired = cand_days[cand_scores >= threshold]
        if len(fired):
            detected += 1
            leads.append(event_day - fired.min())
    return {
        "customers_with_event": total_positive_customers,
        "detected_before_event": detected,
        "detection_rate": detected / total_positive_customers if total_positive_customers else 0.0,
        "mean_lead_time_days": float(np.mean(leads)) if leads else None,
        "median_lead_time_days": float(np.median(leads)) if leads else None,
    }


def run(txns: pd.DataFrame, custs: pd.DataFrame, seed: int = 42) -> dict:
    start = txns["date"].min()
    n_days = int((txns["date"].max() - start).days) + 1

    unique_merchants = txns["true_merchant_canonical"].unique().tolist()
    affinity = merchant_affinity(unique_merchants, _embed_fn)

    features = build_all_features(txns, start, n_days, affinity)

    has_baby = dict(zip(custs["customer_id"], custs["has_baby_event"]))
    baby_day_map = {}
    for _, r in custs[custs["has_baby_event"]].iterrows():
        baby_day_map[int(r["customer_id"])] = int((pd.Timestamp(r["baby_event_date"]) - start).days)

    customer_ids = list(features.keys())
    checkpoints = make_checkpoints(customer_ids, has_baby, baby_day_map, n_days)
    print(f"{len(checkpoints):,} checkpoints, {checkpoints['label'].mean():.3f} positive rate")

    # customer-level split (GroupKFold, one fold) so no customer's own
    # history leaks between train and test
    gkf = GroupKFold(n_splits=5)
    idx = np.arange(len(checkpoints))
    train_idx, test_idx = next(gkf.split(idx, groups=checkpoints["customer_id"]))
    train_cp, test_cp = checkpoints.iloc[train_idx], checkpoints.iloc[test_idx]

    # --- incumbent rule ---
    incumbent_preds = np.array([
        incumbent_rule_score(features[r.customer_id], r.as_of_day, HEALTH_COL, AFFINITY_COL)
        for r in test_cp.itertuples()
    ])
    incumbent_metrics = dict(
        precision=float(precision_score(test_cp["label"], incumbent_preds, zero_division=0)),
        recall=float(recall_score(test_cp["label"], incumbent_preds, zero_division=0)),
    )
    incumbent_scores_by_cust = {c: [] for c in customer_ids}
    incumbent_days_by_cust = {c: [] for c in customer_ids}
    for r in checkpoints.itertuples():
        incumbent_scores_by_cust[r.customer_id].append(
            1.0 if incumbent_rule_score(features[r.customer_id], r.as_of_day, HEALTH_COL, AFFINITY_COL) else 0.0)
        incumbent_days_by_cust[r.customer_id].append(r.as_of_day)
    incumbent_lead = lead_time_days(
        {c: np.array(v) for c, v in incumbent_scores_by_cust.items()},
        {c: np.array(v) for c, v in incumbent_days_by_cust.items()},
        baby_day_map, threshold=0.5)

    # --- GBDT over flattened window aggregates ---
    import lightgbm as lgb
    X_train_gbdt = np.stack([window_aggregates(features[r.customer_id], r.as_of_day) for r in train_cp.itertuples()])
    X_test_gbdt = np.stack([window_aggregates(features[r.customer_id], r.as_of_day) for r in test_cp.itertuples()])
    gbdt = lgb.LGBMClassifier(
        n_estimators=100, max_depth=2, num_leaves=7, min_child_samples=20,
        reg_lambda=5.0, learning_rate=0.05, class_weight="balanced", verbosity=-1,
    )
    gbdt.fit(X_train_gbdt, train_cp["label"])
    gbdt_train_proba = gbdt.predict_proba(X_train_gbdt)[:, 1]
    gbdt_test_proba = gbdt.predict_proba(X_test_gbdt)[:, 1]
    gbdt_threshold = _best_f1_threshold(train_cp["label"].to_numpy(), gbdt_train_proba)
    gbdt_preds = gbdt_test_proba >= gbdt_threshold
    gbdt_metrics = dict(
        precision=float(precision_score(test_cp["label"], gbdt_preds, zero_division=0)),
        recall=float(recall_score(test_cp["label"], gbdt_preds, zero_division=0)),
        threshold=gbdt_threshold,
    )

    # --- GRU over the raw 90-day sequence ---
    import torch
    from torch import nn

    class GRUClassifier(nn.Module):
        def __init__(self, n_features, hidden=32):
            super().__init__()
            self.gru = nn.GRU(n_features, hidden, batch_first=True)
            self.head = nn.Linear(hidden, 1)

        def forward(self, x):
            _, h = self.gru(x)
            return self.head(h[-1]).squeeze(-1)

    def make_seq_tensor(cp_df):
        seqs = np.stack([window_sequence(features[r.customer_id], r.as_of_day) for r in cp_df.itertuples()])
        # per-feature standardisation, fit on train only (done by caller)
        return seqs.astype(np.float32)

    X_train_seq = make_seq_tensor(train_cp)
    X_test_seq = make_seq_tensor(test_cp)
    mu, sigma = X_train_seq.mean((0, 1), keepdims=True), X_train_seq.std((0, 1), keepdims=True) + 1e-6
    X_train_seq = (X_train_seq - mu) / sigma
    X_test_seq = (X_test_seq - mu) / sigma

    torch.manual_seed(seed)
    model = GRUClassifier(n_features=len(FEATURE_COLS))
    y_train_t = torch.tensor(train_cp["label"].to_numpy(), dtype=torch.float32)
    pos_weight = torch.tensor((y_train_t == 0).sum() / max((y_train_t == 1).sum(), 1))
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optim = torch.optim.Adam(model.parameters(), lr=1e-3)

    X_train_t = torch.tensor(X_train_seq)
    n = len(X_train_t)
    batch_size = 256
    for epoch in range(8):
        model.train()
        perm = torch.randperm(n)
        total_loss = 0.0
        for i in range(0, n, batch_size):
            batch_idx = perm[i:i + batch_size]
            optim.zero_grad()
            logits = model(X_train_t[batch_idx])
            loss = criterion(logits, y_train_t[batch_idx])
            loss.backward()
            optim.step()
            total_loss += loss.item() * len(batch_idx)
        print(f"  GRU epoch {epoch}: loss={total_loss/n:.4f}")

    model.eval()
    with torch.no_grad():
        gru_train_proba = torch.sigmoid(model(X_train_t)).numpy()
        gru_test_proba = torch.sigmoid(model(torch.tensor(X_test_seq))).numpy()
    gru_threshold = _best_f1_threshold(train_cp["label"].to_numpy(), gru_train_proba)
    gru_preds = gru_test_proba >= gru_threshold
    gru_metrics = dict(
        precision=float(precision_score(test_cp["label"], gru_preds, zero_division=0)),
        recall=float(recall_score(test_cp["label"], gru_preds, zero_division=0)),
        threshold=gru_threshold,
    )

    keep_or_drop = "keep GRU" if (
        gru_metrics["precision"] + gru_metrics["recall"] > gbdt_metrics["precision"] + gbdt_metrics["recall"]
    ) else "drop GRU, GBDT wins"

    report = {
        "n_checkpoints": len(checkpoints), "positive_rate": float(checkpoints["label"].mean()),
        "n_baby_event_customers": len(baby_day_map),
        "incumbent_rule": {**incumbent_metrics, "lead_time": incumbent_lead},
        "gbdt_aggregates": gbdt_metrics,
        "gru_sequence": gru_metrics,
        "keep_or_drop_gru_vs_gbdt": keep_or_drop,
    }
    out_path = Path(__file__).parent / "report_life_events.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    from app.ml.population import generate_population
    txns, custs = generate_population(n_customers=800, months=12, seed=42)
    run(txns, custs)
