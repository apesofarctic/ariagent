# AriAgent ML layer: build and evaluation plan

**Brief being served.** SBI Global Fintech Fest 2026: acquire customers, drive digital
adoption, create meaningful engagement, using agentic AI. That is a targeting and
sequencing problem (who to reach, with what, when, and when to stay quiet), not a
chatbot problem. The ML layer below decides who/what/when; the agentic layer acts and
explains; the grounding layer keeps the language honest.

**Governing rule.** Every component is measured against the incumbent it would replace.
If the incumbent wins, the incumbent stays and the report says so. A challenger that
loses is a finding, not a failure, and it gets reported as one.

**Honesty perimeter.** No bank ran this. No customer ever received a nudge from it. The
population, the response behaviour and the randomised nudge log are simulated, and every
number derived from them describes a modelled population. The only externally real
artifact is the grounding corpus: 528 passages parsed from RBI's own customer FAQ pages.

```
Sense      transaction understanding      phase 1   -> bullet 1
Predict    propensity and uplift          phase 2   -> bullet 2
Decide     agentic planner under budget   phase 3   -> bullet 3
Ground     claim verifier                 phase 3
Explain    the card the customer sees
```

---

## Phase 0. Foundations

### 0.1 Population generator  (`backend/app/ml/population.py`)
**Does.** Generates 12,000 synthetic retail customers over 12 months of daily
transactions. Each customer carries latent attributes never exposed to any model:
income band, payroll employer and salary day, rent day and amount, per-category spend
propensity, digital-channel affinity, income volatility, and a life-event schedule.
Merchant strings are emitted the way a real statement carries them, with UPI and POS
prefixes, reference numbers, truncation and city suffixes, because coping with that mess
is exactly what the categoriser has to do.
**Why.** Everything downstream needs a ledger, and a clean ledger would make the rules
baseline look better than it is in the field.
**Test.** Distribution checks: income to spend correlation inside a stated band, share of
customers overdrawn at least once per quarter, category mix against published Indian
retail spend shares, merchant string entropy. Fixed seed, regenerable.

### 0.2 Ground truth  (`backend/app/ml/labels.py`)
**Does.** Because the world is generated, true category, true recurring subscriptions,
true life-event dates and true intervention responsiveness are all known. Labels are
written to a separate file from the ledger.
**Test.** An assertion that no label field appears anywhere in the feature path. This is
the leak guard.

### 0.3 Splits  (`backend/app/ml/splits.py`)
**Does.** Customer-level GroupKFold for model selection, plus a time holdout: fit on
months 1 to 9, evaluate on 10 to 12.
**Why both.** Customer grouping stops a customer appearing in train and test. The time
holdout stops a backward-looking feature seeing its own future.
**Test.** Assert zero customer-id overlap across folds and zero timestamp overlap across
the time boundary.

---

## Phase 1. Sensing  (bullet 1)

### 1.1 Incumbent: the shipped rules categoriser
**Does.** Runs `backend/app/categorize.py`'s rules table over raw merchant strings and
scores it against true categories. This is the number to beat.
**Metric.** Macro-F1, per-class recall, and coverage (share of strings left as `other`).

### 1.2 Merchant-string normaliser  (`backend/app/ml/merchants.py`)
**Does.** Strips payment-rail prefixes, reference numbers and city suffixes to a
canonical merchant key.
**Why.** It lifts the rules baseline too. Giving the incumbent its best shot is the point;
beating a strawman proves nothing.
**Test.** Distinct raw strings collapsed per true merchant, and a 100-sample manual read.

### 1.3 Challenger: embedding classifier  (`backend/app/ml/categorizer.py`)
**Does.** Encodes canonical merchant strings with `bge-small-en-v1.5` (384d, ONNX, CPU),
fits a linear classifier on top, with kNN over the embedding space for the long tail.
**Why it matters to the product.** Every detector downstream keys off category. A wrong
category is a wrong nudge.
**Metric.** Macro-F1 against 1.1 and 1.2 on held-out customers, per-class confusion on the
four classes that drive detectors (subscription, salary, rent, health), bootstrap CI on
the margin.
**Keep-or-drop.** If the margin over normalised rules does not clear its CI, the rules
stay and the card reports the rules.

### 1.4 Recurring and duplicate-subscription detection  (`backend/app/ml/recurring.py`)
**Does.** Per (customer, canonical merchant): inter-arrival regularity, amount stability,
run length, and embedding similarity between merchant keys to catch near-duplicates
(`NETFLIX` against `Netflix Premium`). Rule incumbent is the shipped
`duplicate_subscription.py`.
**Metric.** Precision and recall on true subscriptions, and separately on the duplicate
pairs, which is the Protect claim the demo makes.

### 1.5 Life-event detection  (`backend/app/ml/life_events.py`)
**Does.** Sequence model over the 90 days preceding a labelled life event. Each day is a
category-spend vector plus the centroid of that day's merchant embeddings. A small GRU or
temporal CNN in PyTorch, against two baselines: the shipped hardcoded pattern rule, and
gradient boosting over aggregate window features.
**Metric.** Precision and recall at the operating point, and **lead time in days**. Lead
time is the metric that matters: firing after the baby has arrived is worthless.
**Keep-or-drop.** The sequence model is kept only if it beats the GBDT on aggregates.

---

## Phase 2. Targeting  (bullet 2)

### 2.1 Response simulator  (`backend/app/ml/response.py`)
**Does.** Defines, per intervention type, the true probability a customer acts when
nudged and when not nudged, as a function of latent state. Produces the four uplift
quadrants in known proportions: persuadables, sure things, lost causes, and sleeping dogs
(customers whose engagement *drops* when contacted).
**This is the honesty hinge.** It is an assumption set, not observed behaviour, and the
report states so at the top of the section.
**Test.** The four quadrants exist at the intended proportions, and no feature exposed to
any model encodes the quadrant directly.

### 2.2 Randomised nudge log  (`backend/app/ml/nudge_log.py`)
**Does.** Runs a randomised contact policy across the 12 months: every eligible
customer-day-intervention triple is treated with fixed probability. Records treatment and
outcome. This is the training data for uplift.
**Test.** Covariate balance between treated and control (standardised mean differences
near zero). Without balance, uplift is not estimable, so this test gates phase 2.

### 2.3 Incumbent: propensity ranking
**Does.** LightGBM predicting response among the treated, which is what the current card
claims (customer-day ranking over backward-looking features).
**Metric.** AUC, PR-AUC, precision at a stated contact budget.

### 2.4 Challenger: uplift models  (`backend/app/ml/uplift.py`)
**Does.** T-learner (two LightGBM models), S-learner, and X-learner over the same
features.
**Metric.** Qini curve and Qini coefficient, uplift at k, and the comparison that answers
the brief: **expected incremental actions per 1,000 contacts under propensity ranking
against uplift ranking**. Propensity ranks who will act. Uplift ranks who acts *because*
you contacted them. The gap between those two numbers is the difference between
engagement and spam.
**Test.** Customer-level holdout, bootstrap CIs on Qini, and a negative control: shuffle
the treatment assignment and confirm Qini collapses toward zero.

### 2.5 Contact policy under budget and fatigue  (`backend/app/ml/policy.py`)
**Does.** Given uplift scores across intervention types per customer-day, choose the
assignment maximising incremental actions subject to a budget of B contacts per 1,000
customer-days and a per-customer cooldown. Greedy against a small knapsack solve.
**Metric.** Incremental actions per 1,000 against the policy the repo ships (fire whenever
a detector trips), plus the **suppression rate**: the share of detector firings the policy
silences. This turns the demo's restraint into a number.

---

## Phase 3. Agentic layer and grounding  (bullet 3)

### 3.1 Typed tool suite  (`backend/app/agentic/tools.py`)
**Does.** Wraps real capabilities as JSON-schema'd tools returning structured data, never
prose: `get_forecast`, `list_transactions`, `find_recurring`, `score_interventions`,
`retrieve_policy`, `propose_action`.
**Test.** Schema validation on every call, with a per-run tool-call log.

### 3.2 Planner loop  (`backend/app/agentic/planner.py`)
**Does.** Local `qwen2.5:3b` via Ollama plans which tools to call for a given customer-day
and drafts the card. Incumbent is the shipped fixed five-agent chain.
**Metric.** Correct-action rate on scripted scenarios with known correct outcomes,
invalid tool-call rate, mean tools per task, and a failure-mode breakdown.
**Keep-or-drop.** If the planner does not beat the fixed chain, the report says the fixed
chain won. A 3B model losing to a deterministic chain is a publishable result, not an
embarrassment.

### 3.3 Grounding gate  (`backend/app/agentic/verifier.py`)
**Does.** Extracts atomic claims from each drafted card and routes them. Numeric claims
("you will be short Rs.4,200 on the 28th") are checked against the ledger and the
forecast. Procedural claims ("the bank must refund an unauthorised debit within 10 days")
are checked against the RBI passages by retrieval plus cross-encoder entailment.
Unsupported claims are dropped, and the card either abstains or cites.
**Metric.** Unsupported-claim rate before and after the gate, gate precision (how often it
blocks a claim that was in fact supported), and abstention rate. Threshold calibrated on a
dev split and reported on a test split.
**Incumbent.** The rule plus logistic regression verifier from the September analysis,
scored on the same claim set.

### 3.4 Retrieval bake-off, scoped to procedural claims  (`evals/eval_retrieval.py`)
**Does.** BM25, dense `bge-base-en-v1.5` (768d), SPLADE++, RRF fusion, and fusion plus
`bge-reranker-base` cross-encoder, over the 528 RBI passages.
**Two query tracks.** Track A is the official FAQ question against an answer-only index,
so lexical search cannot win by copying the question back. Track B is customer-voice
paraphrase, which is the gap lexical search cannot close.
**Metric.** recall@1/3/5, MRR, nDCG, p50 latency. Keep the cheapest configuration that is
within noise of the best.

---

## Phase 4. Report and card

- **4.1** `evals/run_all.py` writes `evals/report.md` and `report.json`: every table, model
  version, seed, runtime, and corpus fingerprint.
- **4.2** A keep-or-drop table covering all six incumbent-against-challenger comparisons,
  each with its margin and CI.
- **4.3** Draft the three bullets from winning numbers only, then fit each to the CV2
  width rule (x1 in [579.7, 580.7]) with `.cvfit/width.py`.
- **4.4** Update `cvpointerdata.txt` row 25, add CV2 section 8.5, and refresh the defense
  pack and interview questions in `_work/packages/ariagent.json`.

## Costs and risks

- ONNX model downloads: bge-small, bge-base, SPLADE++, bge-reranker-base.
- Ollama on CPU is the slow path. Phase 3 scenario count is capped near 100 tasks per
  condition to keep a full sweep inside a single run.
- PyTorch work is small (a GRU over 90-day windows), CPU is sufficient.
- Largest risk to credibility is 2.1. If the response simulator is tuned until uplift
  looks good, the number means nothing. It is written and frozen before any uplift model
  is fitted, and the report states its parameters in full.
