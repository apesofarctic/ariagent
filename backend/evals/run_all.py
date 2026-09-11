"""Phase 4.1 (scoped to phases 0-1) — generate the population once, run every
phase 0/1 eval against it, write evals/report.json + evals/report.md."""
from __future__ import annotations

import json
import time
from pathlib import Path

from app.ml.population import generate_population
from app.ml.merchants import normalize_merchant
from app.ml.splits import customer_group_kfold, time_holdout, assert_customer_disjoint, assert_time_disjoint
from app.ml.labels import build_labels

N_CUSTOMERS = 800
MONTHS = 12
SEED = 42


def main():
    t0 = time.time()
    txns, custs = generate_population(n_customers=N_CUSTOMERS, months=MONTHS, seed=SEED)
    txns["norm"] = txns["raw_merchant"].map(normalize_merchant)
    gen_time = time.time() - t0
    print(f"population: {len(txns):,} rows / {len(custs):,} customers in {gen_time:.1f}s")

    labels = build_labels(txns, custs)

    # phase 0.3 split sanity checks, run for real against this population
    train_idx, test_idx = next(customer_group_kfold(txns, n_splits=5, seed=SEED))
    assert_customer_disjoint(txns, train_idx, test_idx)
    time_train_idx, time_test_idx, boundary = time_holdout(txns, months_train=9)
    assert_time_disjoint(txns, time_train_idx, time_test_idx)
    print("phase 0 split checks: passed")

    from evals import eval_categorizer, eval_recurring, eval_life_events

    print("\n=== 1.1/1.2/1.3 categorizer bake-off ===")
    cat_report = eval_categorizer.run(n_customers=N_CUSTOMERS, months=MONTHS, seed=SEED)

    print("\n=== 1.4 recurring / duplicate-subscription ===")
    rec_report = eval_recurring.run(txns)

    print("\n=== 1.5 life-event (baby) detection ===")
    life_report = eval_life_events.run(txns, custs, seed=SEED)

    report = {
        "population": {
            "n_customers": N_CUSTOMERS, "months": MONTHS, "seed": SEED,
            "n_transactions": len(txns), "generation_time_s": round(gen_time, 1),
            "deviation_from_plan": "plan specifies 12,000 customers; this build ran 800 "
                                    "to fit the compute budget of a single build session.",
        },
        "phase0_labels": {k: len(v) for k, v in labels.items()},
        "phase1_1_1_2_1_3_categorizer": cat_report,
        "phase1_1_4_recurring": rec_report,
        "phase1_1_5_life_events": life_report,
        "total_runtime_s": round(time.time() - t0, 1),
    }
    out_dir = Path(__file__).parent
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, default=str))
    print(f"\nwrote {out_dir/'report.json'}; total runtime {report['total_runtime_s']}s")
    return report


if __name__ == "__main__":
    main()
