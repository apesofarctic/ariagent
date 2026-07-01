# Ariagent — Brief Description of the Idea (Deliverable #3)

> This is the spine of the whole submission. Two versions below: a tight **submission-box version** (paste into the form) and a **long version** (source material for the deck and talk track).

---

## A. Submission-box version (~200 words — paste this)

**Ariagent — a proactive, agentic financial companion that Protects, Grows, and Guides.**

Today's banking AI is reactive: it waits for the customer to open the app and ask. Ariagent inverts this. It is an always-on multi-agent system that continuously watches a customer's financial signals — transactions, balances, recurring debits, merchant patterns — and **acts first**, across three modes:

- **Protect** — forecasts overdrafts, catches duplicate subscriptions and fraud, and reaches out *before* harm ("Your rent debits before your salary lands this month — shift it?").
- **Grow** — detects idle cash and income changes and puts money to work ("Your salary rose ₹15k — auto-invest ₹5k/month?").
- **Guide** — recognises life events from spending (a baby, a new job, a home) and orchestrates a multi-step journey of insurance, savings and investments.

Five specialised agents — Sentinel, Insight, Orchestrator, Engagement, Action — sense, reason, prioritise, and execute one-tap actions, **showing their reasoning on every recommendation**. A guardrail layer enforces suitability, consent, and reversibility. The same engine powers acquisition and adoption too, making Ariagent a platform, not a feature. Engagement becomes something the bank *does for* the customer, not something it sells.

---

## B. Long version (deck + talk-track source)

### The problem
Banks spend enormously on digital channels, yet engagement is shallow and reactive. The app is a destination the customer must choose to visit, and when they do, it answers questions they already knew to ask. The result:
- **Harm goes uncaught** — overdrafts, forgotten subscriptions, and fraud are noticed *after* the money is gone.
- **Opportunity is missed** — idle balances and income changes sit unaddressed; the customer never gets "ahead."
- **Life's big moments are unsupported** — exactly when a customer most needs the bank (a baby, a new home, a job change), the bank is silent because no one filled out a form.

Generic push notifications and rule-based "nudges" don't fix this — they're untimed, impersonal, and quickly muted. The missing capability is **judgment**: knowing *what* matters to *this* customer, *right now*, and *what to do about it.*

### The idea
**Ariagent is a proactive financial companion that acts first and explains itself.** It treats engagement as a continuous agentic loop rather than a notification feed:

> **Sense → Reason → Decide → Act → Explain**

It runs that loop over three classes of signal, which become its three modes:

1. **PROTECT (Threats).** Overdraft forecasting, duplicate/zombie subscriptions, bill spikes, anomalous/fraudulent transactions, cashflow gaps. Action: shift a debit date, cancel a duplicate, arrange a buffer, lock a card.

2. **GROW (Opportunities).** Idle cash, recurring surplus, salary hikes, round-up potential. Action: start an SIP, sweep to high-yield, fund a goal.

3. **GUIDE (Life Events).** Patterns that reveal a baby, a new job, a relocation, a wedding, approaching retirement. Action: launch a **multi-step journey** — e.g., a detected pregnancy triggers an emergency-fund top-up, a health-insurance review, and a goal-based savings plan, sequenced over weeks rather than dumped at once.

### Why it's genuinely *agentic* (not a chatbot, not a rules engine)
Three properties separate Ariagent from a notification system:

- **It's autonomous and proactive** — it initiates, the customer doesn't.
- **It reasons and prioritises** — the **Orchestrator** decides *which* signal deserves attention now, holds back lower-value nudges, and interleaves a slow multi-week journey with an urgent alert. It will deliberately stay silent to avoid spam. That judgment *is* the product.
- **It's accountable** — every recommendation carries a **visible reasoning trace** ("salary credit +₹15k × 2 months → ₹9k recurring surplus → SIP recommended"), and every action is suitability-checked, consented, reversible, and audited.

### What the customer experiences
A companion that quietly has their back: it warns them before the overdraft, cancels the subscription they forgot, finds the surplus they didn't notice, and walks them through the big moments — always with a one-tap action and a plain-English "here's why." Over time, as trust builds, the customer can let Ariagent handle classes of decisions on its own (the **Pulse** autopilot tier).

### Why it matters to the bank
Every mode maps to a revenue lever (retention, AUM, cross-sell), and the same engine generalises to customer acquisition and digital adoption — so a single architecture answers all three of the hackathon's problem statements. (Detail in the business-model doc.)
