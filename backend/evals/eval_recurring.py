"""Phase 1.4 — recurring / duplicate-subscription eval."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score

from app.ml.merchants import normalize_merchant
from app.ml.recurring import build_groups, classify_recurring, find_duplicate_pairs, incumbent_duplicate_rule


def _embed_fn(texts):
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", threads=8)
    return np.array(list(model.embed(list(texts), batch_size=64)))


def true_alias_duplicate_customers(txns: pd.DataFrame) -> set[int]:
    """customers where >=1 canonical subscription service shows up under
    more than one normalized merchant key — the genuine 'needs a merge' case."""
    subs = txns[txns["true_category"] == "subscription"]
    per_service = subs.groupby(["customer_id", "true_merchant_canonical"])["norm"].nunique()
    return set(per_service[per_service > 1].index.get_level_values("customer_id"))


def run(txns: pd.DataFrame) -> dict:
    txns = txns.copy()
    txns["norm"] = txns["raw_merchant"].map(normalize_merchant)

    groups = build_groups(txns, key_col="norm")
    pred_recurring = classify_recurring(groups)
    sub_precision = precision_score(groups["true_is_subscription"], pred_recurring, zero_division=0)
    sub_recall = recall_score(groups["true_is_subscription"], pred_recurring, zero_division=0)

    true_dup_customers = true_alias_duplicate_customers(txns)
    all_customers = set(txns["customer_id"].unique())

    pair_preds = find_duplicate_pairs(groups, _embed_fn)
    challenger_flagged = set(pair_preds.loc[pair_preds["predicted_duplicate"], "customer_id"])

    incumbent_raw = incumbent_duplicate_rule(txns, merchant_col="raw_merchant")
    incumbent_raw_flagged = set(incumbent_raw.loc[incumbent_raw["fired"], "customer_id"])

    incumbent_norm = incumbent_duplicate_rule(txns, merchant_col="norm")
    incumbent_norm_flagged = set(incumbent_norm.loc[incumbent_norm["fired"], "customer_id"])

    def prf(flagged: set[int]) -> dict:
        y_true = [c in true_dup_customers for c in all_customers]
        y_pred = [c in flagged for c in all_customers]
        return dict(
            precision=float(precision_score(y_true, y_pred, zero_division=0)),
            recall=float(recall_score(y_true, y_pred, zero_division=0)),
            n_flagged=len(flagged),
        )

    report = {
        "n_customers": len(all_customers),
        "n_groups": len(groups),
        "recurring_subscription_detection": {"precision": float(sub_precision), "recall": float(sub_recall)},
        "n_true_alias_duplicate_customers": len(true_dup_customers),
        "duplicate_pairs": {
            "incumbent_rule_on_raw_strings": prf(incumbent_raw_flagged),
            "incumbent_rule_on_normalized_strings": prf(incumbent_norm_flagged),
            "challenger_embedding_similarity": prf(challenger_flagged),
        },
    }
    out_path = Path(__file__).parent / "report_recurring.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    from app.ml.population import generate_population
    txns, custs = generate_population(n_customers=800, months=12, seed=42)
    run(txns)
