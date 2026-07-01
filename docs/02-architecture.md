# Ariagent — Process Flow & Architecture (Deliverable #6)

> The technical spine. The headline: **one shared agent pipeline + two pluggable libraries** (Detectors and Actions). The three modes — Protect, Grow, Guide — are not three systems; they are three sets of registered detectors/actions flowing through the same brain.

---

## 1. The core loop

```
   Sense  →  Reason  →  Decide  →  Act  →  Explain
 (Sentinel) (Insight) (Orchestr.) (Action) (Engagement + trace)
```

Engagement becomes a continuous loop, not a notification feed. Every customer event runs this loop; most of the time the right decision is **do nothing** (the Orchestrator's restraint is a feature).

---

## 2. System diagram

```
        ┌───────────────────── SIGNALS (inputs) ────────────────────┐
        │  transaction stream · balances · recurring-debit calendar  │
        │  merchant/category data · goals · profile ("financial twin")│
        └───────────────────────────┬───────────────────────────────┘
                                     ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │ 1. SENTINEL AGENT  — Sense                                        │
   │    Runs the DETECTOR LIBRARY across all three domains:            │
   │      Protect: overdraft-forecast · dup-subscription · fraud ·     │
   │               bill-spike · cashflow-gap                           │
   │      Grow:    surplus · idle-cash · salary-hike · roundup         │
   │      Guide:   baby-spend · new-job · rent→mortgage · wedding ·    │
   │               relocation                                          │
   │    → emits typed SIGNAL { type, mode, confidence, evidence[] }    │
   └────────────────────────────────┬─────────────────────────────────┘
                                     ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │ 2. INSIGHT AGENT  — Reason                                        │
   │    Per signal: relevance · urgency · confidence · intent (P/G/G)  │
   │    · cashflow forecast · expected value. Discards noise.          │
   │    Attaches the human-readable "why" (evidence → reasoning).      │
   └────────────────────────────────┬─────────────────────────────────┘
                                     ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │ 3. ORCHESTRATOR AGENT  — Decide   ◀── the brain that unifies      │
   │    • Prioritises across competing signals                        │
   │      (urgent Protect ≻ nice-to-have Grow)                         │
   │    • Frequency caps + quiet hours  → ANTI-SPAM / suppression      │
   │    • Sequences & tracks multi-step GUIDE journeys (state machine) │
   │    • Chooses channel + timing                                     │
   │    → outputs a DECISION: fire | hold | suppress | sequence        │
   └───────────────┬────────────────────────────────┬─────────────────┘
                   ▼ (fire)                          ▼ (on approval)
   ┌──────────────────────────────┐   ┌──────────────────────────────┐
   │ 4. ENGAGEMENT AGENT — Explain│   │ 5. ACTION AGENT — Act         │
   │    Writes personalised nudge │──▶│    Executes via BANKING TOOLS:│
   │    + one-tap action card     │   │      move_money · shift_debit │
   │    + visible reasoning trace │   │      start_sip · lock_card ·  │
   │                              │   │      buy_insurance · open_goal│
   └──────────────────────────────┘   │      · cancel_subscription    │
                                       └───────────────┬───────────────┘
                                                       ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  GUARDRAIL / COMPLIANCE LAYER  (cross-cutting on every action)    │
   │  suitability check · consent · reversibility · full audit log     │
   └──────────────────────────────────────────────────────────────────┘
                                     │
                           ┌─────────┴──────────┐
                           │  MEMORY / STATE     │
                           │  profile · goals ·  │
                           │  journey state ·    │
                           │  nudge history ·    │
                           │  preferences        │
                           └─────────────────────┘
```

---

## 3. The agents (responsibilities + I/O)

| Agent | Role in loop | Input | Output | Why it's an agent (not a function) |
|---|---|---|---|---|
| **Sentinel** | Sense | raw signal stream | typed Signals w/ evidence | Pattern recognition over noisy, ambiguous data; new detectors added without code rewrite |
| **Insight** | Reason | a Signal | scored, classified, explained Insight | Judges relevance/urgency/value in context of *this* customer |
| **Orchestrator** | Decide | all pending Insights + history + prefs | a Decision (fire/hold/suppress/sequence) | The hard agentic problem: what to surface, when, how often, in what order |
| **Engagement** | Explain | a fired Decision | personalised card + reasoning trace | Hyper-personalised natural-language generation |
| **Action** | Act | approved action | tool calls + result | Tool-use against banking APIs with guardrails |

---

## 4. The two pluggable libraries (why the modes unify)

**Detector Library** — each detector is `signals_in → Signal | null`. Registered by mode. Examples:
- `overdraft_forecast` (Protect): projects balance vs. scheduled debits → fires if projected balance < 0.
- `recurring_surplus` (Grow): rolling income − essential spend > threshold for N periods.
- `life_event_baby` (Guide): clinic + pharmacy + category shifts → probabilistic life-event signal.

**Action Library** — each action is a guarded `tool` the Action Agent can call: `shift_debit_date`, `cancel_subscription`, `start_sip`, `sweep_to_high_yield`, `open_goal`, `buy_insurance`, `lock_card`, `arrange_buffer`.

Adding a mode or capability = registering detectors + actions. **No pipeline changes.** This is the architectural claim that makes "three modes, one product" true.

---

## 5. Data model (prototype)

```
Customer      { id, profile, financial_twin, preferences, quiet_hours }
Transaction   { id, date, amount, merchant, category, balance_after }
RecurringDebit{ id, label, amount, day_of_month }
Signal        { id, type, mode, confidence, evidence[], detected_at }
Insight       { signal_id, relevance, urgency, value, rationale }
Decision      { insight_id, verdict: fire|hold|suppress|sequence, reason }
ActionCard    { decision_id, title, body, action, reasoning_trace }
ActionResult  { card_id, tool, params, status, reversible, audit_id }
Journey       { id, type, steps[], current_step, state }
```

---

## 6. Multi-step GUIDE journeys (the state machine)

A life event doesn't fire one nudge — the Orchestrator instantiates a **Journey** and advances it over time:

```
"New Baby" Journey
  step 1  →  Emergency-fund top-up      (offer, await accept)
  step 2  →  Health-insurance review    (after step 1, +days)
  step 3  →  Goal-based savings plan    (after step 2, +days)
  guard:    pause/resume on cashflow stress; never stack steps
```

This is what distinguishes GUIDE from a one-shot nudge, and it's why the Orchestrator holds journey *state*.

---

## 7. The Orchestrator's suppression logic (the differentiator)

Pseudocode of the decision the demo highlights on Day 27:

```
decide(pending_insights, history, prefs):
    rank = sort(pending_insights, by = urgency * value * confidence)
    if recent_nudges(history) >= prefs.frequency_cap:        → suppress all but CRITICAL
    if now in prefs.quiet_hours:                              → hold until window
    top = rank[0]
    for others in rank[1:]:
        if others.value < top.value * MATERIALITY_RATIO:     → suppress (don't dilute)
    return fire(top); hold/suppress the rest with logged reasons
```

Every suppression is logged with its reason and shown in the agent log — proving the system exercises *restraint*, the hallmark that separates an agent with judgment from a rule engine that fires on every match.

---

## 8. Trust ladder (how autonomy scales — roadmap)

```
Tier 1  Suggest        Ariagent recommends → user one-tap approves   ◀ MVP/demo
Tier 2  Standing rules user pre-authorises a class within limits
Tier 3  Pulse          full delegation + weekly "what I did & why"
```

The same pipeline supports all three; only the **consent scope** at the guardrail layer changes.

---

## 9. Reference tech stack (to finalise at Phase 2)

- **Agents / orchestration:** Claude (Opus/Sonnet) with tool-use for the agent loop; a thin orchestration layer in Python.
- **Backend:** FastAPI (Python) — agent endpoints, signal bus, audit log.
- **Frontend:** Next.js + React + Tailwind dashboard (timeline, action cards, live reasoning traces). *(Streamlit is the fast-path alternative.)*
- **Data:** synthetic transaction generator seeded with the planted Priya signals; in-memory or SQLite store for the prototype.
- **Demo mode:** live Claude when an `ANTHROPIC_API_KEY` is present; scripted fallback for offline/venue-wifi safety.
