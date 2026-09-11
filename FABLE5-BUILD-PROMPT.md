# Fable 5 build prompt — Ariagent finished product

> Copy everything below the line into Fable 5. It is a self-contained brief. It assumes the repo at
> `/home/chloe/projects/ariagent` already contains a working backend + basic frontend (described inline),
> and asks you to turn it into a polished, demo-ready product with a real design system and two data modes.

---

You are building the finished, demo-ready version of **Ariagent** — a proactive, multi-agent financial
companion. A working prototype already exists in this repo; **build on it, do not start from scratch or
rewrite the agent logic.** Your job is (1) a genuinely well-designed UI, (2) two data modes
(demo/dummy vs. real), and (3) the compliance UX. Read `docs/05-legal-compliance.md` in this repo — it is
binding; the compliance features listed there are requirements, not suggestions.

## What Ariagent is (context)
An always-on system that watches a customer's transactions and **acts first** across three modes:
**Protect** (overdraft/fraud/duplicate-subscription), **Grow** (idle cash, salary hikes → SIP), and
**Guide** (life events like a new baby → multi-step journeys). Five agents run a loop —
**Sentinel → Insight → Orchestrator → Engagement → Action** (Sense → Reason → Decide → Act → Explain) —
and the product's signature is that it **shows its reasoning live** and exercises **restraint**
(the Orchestrator suppresses low-value nudges). Full idea in `docs/01-idea-description.md`; architecture
in `docs/02-architecture.md`.

## Existing stack — keep it, extend it
- **Backend:** Python FastAPI at `backend/app`. The 5-agent pipeline is implemented
  (`agents/`, `detectors/`, `guardrails.py`, `tools.py`, `pipeline.py`). It streams the agent loop over
  **SSE** at `GET /api/stream`, and serves `GET /api/profile`, `GET /api/transactions`. The LLM layer
  (`llm.py`) targets an **OpenAI-compatible endpoint**; it is currently **Ollama running
  `qwen2.5:3b` locally** (see `backend/.env`: `LLM_MODEL=qwen2.5:3b`). Correctness-critical math
  (overdraft forecast, suppression) is **deterministic Python** — keep it that way; the local model is
  only for language/classification. `USE_LLM=false` must keep everything working (deterministic text).
- **Frontend:** Next.js (App Router, TypeScript, Tailwind v4, framer-motion) in `frontend/`. Currently a
  single dark page (`src/app/page.tsx`) with a "Run agent loop" button and a plain event list. Replace
  this with the real product UI below. `NEXT_PUBLIC_API_URL` points at the backend.

## Design system — blue / green / gray (this is the core ask)
Design a clean, modern, **fintech-grade** interface. Not a toy, not a generic dashboard template — it
should read like a product a bank would ship. Use exactly this palette philosophy:

- **Green = Protect + safety + money-is-OK.** Primary accent for the Protect mode, positive balances,
  "you're safe / handled" states, confirmations. (e.g. emerald/teal family.)
- **Blue = Grow + primary brand + trust.** The brand/primary color, the Grow mode, primary buttons,
  links, the "growth/opportunity" visuals. (e.g. a confident indigo/sky blue.)
- **Gray = neutral canvas + Guide + structure.** Backgrounds, surfaces, cards, borders, secondary text,
  and the calm/neutral **Guide** mode (a warmer slate). The UI is mostly calm gray; blue and green are
  used with restraint as accents — a lot of gray, a little color.
- Support **light and dark** themes; default to light for the polished screenshots, allow toggle.
- Define this as **CSS variables / a Tailwind theme** (`--color-protect`, `--color-grow`,
  `--color-guide`, `--color-primary`, surface/border/text scales) so mode-coloring is consistent
  everywhere — mode badges, timeline dots, agent-stage chips, and action cards all pull from the same
  tokens. Pick specific, accessible hex values (WCAG AA contrast) and document them.
- Typography: one clean sans (Inter or similar via next/font), clear hierarchy, tabular figures for
  money. Generous whitespace, soft shadows, ~12–16px radii, subtle borders.
- **Motion (framer-motion):** agent events animate in as they stream; the Orchestrator "suppression"
  moment gets a deliberate, distinct treatment (a card that fades/greys out with a "held — here's why"
  reason). Motion should feel intelligent, not busy.

## Screens to build
1. **Onboarding / Consent (gate).** Plain-language purpose, **granular opt-in** toggles for Protect /
   Grow / Guide, adult confirmation, link to privacy notice. No data flows until this passes. (DPDP.)
2. **Dashboard (home).** The hero. Three regions:
   - **Financial snapshot** — balance, upcoming debits, a compact cashflow forecast line/area chart
     (green above buffer, amber/red near overdraft). Follow the `dataviz` skill for any chart.
   - **60-day timeline** — the Priya scenario events plotted by day, dot-colored by mode
     (Protect=green, Grow=blue, Guide=gray/slate), the suppressed nudge visibly greyed.
   - **Live agent reasoning stream** — as `/api/stream` fires, show each stage
     (Sense/Reason/Decide/Explain/Act) with the agent name, its text, and per-mode coloring. This is
     the "wow." One-tap **Action Cards** appear at the Explain/Act stage with the suggested action.
3. **Action cards** — title, plain-English message, the **reasoning trace** ("why"), a one-tap primary
   button (blue), and a secondary "why?" expander. Regulated actions (SIP/insurance/move-money) MUST
   show the disclaimer from the compliance doc and a **Reversible** tag.
4. **Data panel** — the two-mode switch (see below).
5. **"What Ariagent knows about me"** — every inference (esp. life-event) in plain language + evidence,
   each with a "this is wrong / delete" control. (Transparency + correction rights.)
6. **Audit log** — every action: who/what/when/**why**/reversible. Exportable.
7. **Settings** — theme toggle, consent status + **revoke**, `USE_LLM` / demo-mode indicator,
   **Export my data** and **Delete my data** buttons.

## Two data modes (explicit product requirement)
The guiding doctrine (from the compliance doc): **Ariagent is a read-only, on-device analyst — the user
brings their own data, Ariagent does the thinking, the user stays in control of every action.** That is
both the legal shield and the trust story. Add a clear switch in the Data panel:

- **Demo data (default):** uses the built-in synthetic generator, **or** lets the user **upload a CSV**
  of test transactions (columns: `date, amount, merchant, category`) to see how the model reacts.
  Label the whole workspace **"DEMO DATA — not real; nothing is stored or acted on."** Zero compliance
  risk; this is the "test how the model works" path.
- **Import real data (gated) — the primary new feature.** Only reachable after the consent screen. The
  user runs the full analysis on their **own real bank data**, imported (never integrated):
  (a) **Upload your own bank statement** (CSV / Excel / PDF the user exported from their bank) — the
  compliant, no-licence, no-integration path; (b) **Connect via Account Aggregator** — build the
  consent-artefact UI but **stub** it and label "coming soon." Show a persistent **"REAL DATA —
  consented {date}, processed on-device"** banner and a **Revoke & delete** control.
  - **Never** ask for net-banking credentials/OTPs or store full card/account numbers.
  - **Import pipeline (build this):** real statements have no clean `category` column and every bank's
    export differs. So: (i) a **normalizer** that maps the uploaded file's columns → the `Transaction`
    schema (`date, amount, merchant, category`) with a **manual column-mapping UI** fallback for unknown
    formats and a preview-before-import step; (ii) a **categorizer** (merchant → category) using a rules
    table first, then the local `qwen2.5:3b` for the leftovers (classification is a legitimate LLM use).
    All of this runs on-device.
  - **Analyse-only actions:** Mode B never executes. Action cards produce a **prepared instruction / deep
    link** the user completes in their own bank app (e.g. "Open in bank app to shift this debit"). Mock
    tools; no real money moves. This is what keeps Ariagent out of SEBI/IRDAI/RBI-PSP scope.
- **Export & delete (DPDP rights, secondary):** an **Export my data** action downloads everything Ariagent
  holds (transactions + signals/insights/decisions/actions + audit log) as JSON **and** CSV, paired with
  **Delete my data**. Required, but not the headline — the star of Mode B is *import + analysis*.

### Backend work this implies (add, don't break existing endpoints)
- `POST /api/data/upload` — accept CSV/Excel/PDF, return a **parsed preview + detected column mapping**
  for the user to confirm before import; validate rows against the schema.
- `POST /api/data/import` — commit the confirmed mapping, run the **categorizer**, then the pipeline.
- `POST /api/data/mode` — switch demo/real; real requires a valid consent token.
- `POST /api/consent` / `GET /api/consent` — store & return the consent record (scopes + timestamp).
- `GET /api/export` — bundle all data + audit log as JSON (and a CSV variant); `DELETE /api/data` wipes it.
- `GET /api/inferences` — the "what we know about you" list with evidence, for the transparency screen.
- Add a lightweight **SQLite** store (`app/store.py`) for consent, audit log, imported transactions, and
  inferences — the docs already call for SQLite as the prototype store. Keep in-memory demo working.
- Add a **categorizer** module (`app/categorize.py`): rules table + local-LLM fallback; deterministic when
  `USE_LLM=false`.
- Keep the **scripted/deterministic fallback**: the demo must never depend on the model behaving. Ensure
  `USE_LLM=false` and a `?mode=scripted` stream both work.

## Compliance UX (from `docs/05-legal-compliance.md` — required)
Consent-before-data gate · granular per-mode opt-in · disclaimers on regulated action cards ·
Export / Delete my data · consent status + revoke · transparency ("what we know") · audit log ·
human-in-the-loop (nothing auto-executes). These aren't extra credit — the "regulated-domain
credibility" is part of the product story.

## Constraints & acceptance criteria
- Runs fully **locally and free**: backend on Ollama `qwen2.5:3b`, frontend on Next dev server. Document
  the 3-terminal run (Ollama / backend / frontend) in the README.
- Works with the model OFF (`USE_LLM=false`) and with **no real data** — demo mode must be one click from
  a cold start.
- Don't regress the existing SSE pipeline or the deterministic detectors; reuse the schemas in
  `backend/app/schemas.py`.
- Every new screen is responsive and themed (light/dark), uses the blue/green/gray tokens consistently,
  and passes WCAG AA contrast.
- Deliver: the redesigned frontend, the new backend endpoints + SQLite store, an updated README with run
  steps and a short "design system" section (the tokens + what each color means), and a one-paragraph
  note on which compliance features map to which law (cite the compliance doc).

**Success looks like:** from a cold start I can (1) accept consent, (2) click "Load demo data" and watch
the five agents reason live with mode-colored, animated cards including the suppression moment,
(3) behind the consent gate, **import my own real bank statement** — confirm the column mapping, let it
categorize, and watch the agents analyse my actual money and produce *prepared* (never executed) actions,
(4) inspect "what Ariagent knows about me" and the audit log, and (5) export and delete my data — all in a
calm, confident blue/green/gray interface that looks like a bank could ship it.
