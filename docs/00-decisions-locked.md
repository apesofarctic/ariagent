# Ariagent — Locked Decisions (Phase 0)

> One-page source of truth. Everything downstream (deck, prototype, demo, portfolio) must trace back to these. If a later artifact contradicts this page, fix the artifact — not this page — unless we consciously re-decide here.

---

## 1. Theme
**Problem Statement #3 — Digital Engagement.**
Goal (verbatim from brief): *proactively interact with customers based on behaviours, financial patterns, and life events.*

Why this theme: it is the only one of the three that is inherently **proactive**. Customer Acquisition and Digital Adoption are reactive (the customer comes to you). Digital Engagement is the only theme where autonomous agents that **detect → reason → act on their own** are the natural solution — which is exactly the "next-generation agentic" bar the hackathon is judging.

## 2. Product
**Ariagent** — a proactive financial companion built on a single agent engine, with three engagement modes:

- **PROTECT** — watches for risk (overdrafts, fraud, subscription creep, cashflow gaps) and reaches out *before* harm.
- **GROW** — spots opportunity (idle cash, surplus, salary hikes) and turns idle money to work.
- **GUIDE** — detects life events (baby, new job, home, marriage) and orchestrates multi-step journeys.

One-line pitch:
> *Most banking AI waits for you to ask. Ariagent watches your financial life and acts first — protecting you from harm, growing your money, and guiding you through life's big moments — and it shows you exactly why, every time.*

## 3. The core insight (why the three modes are ONE product)
PROTECT, GROW, and GUIDE are not three products. They are the **same loop — Sense → Reason → Decide → Act → Explain — pointed at three classes of signal** (Threats, Opportunities, Life Events). The system is one shared agent pipeline plus two pluggable libraries: a **Detector Library** and an **Action Library**. Adding a mode = registering more detectors and actions, not building a new system.

## 4. Scope cut (MVP vs. Roadmap)
**In the MVP / prototype:**
- 3-mode signal detection over a simulated transaction stream
- Five-agent pipeline (Sentinel → Insight → Orchestrator → Engagement → Action)
- One-tap approved actions with **visible reasoning traces**
- **Orchestrator suppression** (the anti-spam judgment moment — non-negotiable differentiator)
- A light **guardrail layer** (suitability check, consent, reversibility, audit log)

**Out of MVP (roadmap / vision slide):**
- Full **Pulse** autopilot (Tier 3 autonomy — pre-authorized continuous money management)
- Real core-banking / KYC / payment-rail integrations
- Multi-channel delivery (push, WhatsApp, email)

## 5. Staged-autonomy model (the trust ladder)
- **Tier 1 — Suggest** (the demo): Ariagent recommends, user approves in one tap.
- **Tier 2 — Standing rules:** user pre-authorizes a class of action within limits.
- **Tier 3 — Pulse (autopilot):** full delegation + weekly "here's what I did and why" explainer.

Principle: **autonomy in a regulated domain is earned in stages, not switched on.**

## 6. The single demo narrative (everything references this)
**Persona: Priya, 29, salaried.** Just got a ₹15k/month raise — and her spending quietly reveals she is pregnant (before she would ever fill a form). One simulated **60-day timeline** exercises all three modes plus the orchestrator's judgment:

| Day | Mode | Signal | Ariagent acts | Proves |
|---|---|---|---|---|
| 3 | 🛡 Protect | Rent debits on the 5th, salary lands on the 7th → overdraft forecast | Offer to shift debit to the 8th (one tap) | Forecasting + harm prevention |
| 8 | 🛡 Protect | Two subscriptions for the same service | Offer to cancel the duplicate | Subscription creep |
| 14 | 📈 Grow | Salary +₹15k for 2 months, surplus idle | Offer ₹5k/mo SIP | Opportunity capture |
| 22 | 🧭 Guide | Prenatal-clinic + pharmacy pattern → baby life event | Launch "New Baby" journey: emergency fund → health cover → goal savings | Multi-step orchestration |
| 27 | ⚖️ Orchestrator | A low-priority Grow nudge is **suppressed** (two higher-value items pending) | Nothing fires — shown in the agent log | Judgment / anti-spam (the maturity moment) |

## 7. North-star metric
**Proactive Actions Accepted per Active User / month**, balanced against **opt-out / nudge-acceptance rate** (proves helpful, not spammy).

## 8. Open items (to fill later)
- Project title final form — using **"Ariagent"** for now.
- Team details — TBD (user to fill).
- Tech stack — **LOCKED: Next.js + FastAPI + local open-model agents (Ollama + Qwen2.5), provider-agnostic, privacy-first.** See `04-tech-stack.md`.
- Anthropic API key availability for live agents vs. simulated fallback.
