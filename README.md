# Ariagent

**A proactive, agentic financial companion that Protects, Grows, and Guides.**
Hackathon theme: **Digital Engagement** (Problem Statement #3) — *proactively interact based on behaviours, financial patterns, and life events.*

> Most banking AI waits for you to ask. Ariagent watches your financial life and acts first — protecting you from harm, growing your money, and guiding you through life's big moments — and it shows you exactly why, every time.

```
 Sense → Reason → Decide → Act → Explain
(Sentinel)(Insight)(Orchestrator)(Action)(Engagement)

 three modes, one engine:
   🛡 PROTECT   forecast overdrafts, catch fraud & zombie subs — act before harm
   📈 GROW      spot idle cash & income changes — put money to work
   🧭 GUIDE     detect life events — orchestrate multi-step journeys
```

---

## Running it (fully local & free — three terminals)

Prereqs: Python 3.12+, Node 20+, [Ollama](https://ollama.com).

```bash
# Terminal 1 — the local model (optional; everything works without it)
ollama pull qwen2.5:3b
ollama serve

# Terminal 2 — backend (FastAPI on :8000)
cd backend
python -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --port 8000

# Terminal 3 — frontend (Next.js on :3000)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 → accept the consent screen → **Run Ariagent**.

- **No model? No problem.** Set `USE_LLM=false` in `backend/.env` (or leave Ollama off) — all
  text falls back to deterministic templates. Settings → *Scripted runs* forces the same
  per-run (`/api/stream?mode=scripted`), so the demo can never be derailed by the model.
- Money math (overdraft forecast, prioritisation, suppression) is **always deterministic
  Python** — the model only writes language and classifies merchants, locally.

### The five-minute demo

1. Cold start → consent screen (granular Protect/Grow/Guide opt-in, adult gate).
2. Dashboard → **Run Ariagent**: five agents stream their reasoning live; three
   mode-colored action cards fire (shift rent, start SIP, baby journey), the duplicate
   subscription is **held**, the round-up nudge is **suppressed** — restraint on display.
3. **Data → Run it on your actual money**: upload a real bank statement (CSV/XLSX/PDF),
   confirm the auto-detected column mapping, watch it categorise and analyse *your* numbers.
   In real mode nothing executes — cards become **prepared instructions** with a bank-app
   deep link.
4. **What Ariagent knows** → every inference + evidence + "this is wrong — delete".
5. **Audit log** → who/what/when/why/reversible; **Settings** → export (JSON/CSV zip) and
   delete everything.

---

## Two data modes

| | Demo (default) | Real (gated) |
|---|---|---|
| Source | built-in 60-day "Priya" generator, or any test CSV | **your own exported bank statement** (CSV/Excel/PDF); Account Aggregator UI stubbed "coming soon" |
| Banner | `DEMO DATA — not real; nothing is stored or acted on` | `REAL DATA — consented {date}, processed on-device` + **Revoke & delete** |
| Actions | mock tools "execute" | **analyse-only** — prepared instructions the user completes in their own bank app |
| Import pipeline | — | normalizer (auto column-mapping + manual fallback + preview) → categorizer (rules table first, local qwen2.5:3b for leftovers) |

## Design system — blue / green / gray

Tokens live in `frontend/src/app/globals.css` (CSS variables → Tailwind v4 `@theme`), one
source of truth for badges, timeline dots, stage chips, charts and cards. Light and dark are
separately tuned (not auto-flipped); every pairing below is WCAG-AA on its surface and the
trio passes color-blind separation checks as a set.

| Token | Means | Light | Dark |
|---|---|---|---|
| `--protect` | **Green** — Protect, safety, "money is OK", positive states | `#047857` | `#10a56e` |
| `--grow` / `--primary` | **Blue** — brand, Grow, trust, primary buttons & links | `#1d4ed8` | `#5590ee` |
| `--guide` | **Warm bronze-slate** — Guide, life events, calm | `#a16207` | `#bd8b33` |
| `--bg` / `--surface` | **Gray canvas** — the UI is mostly calm gray | `#f4f5f7` / `#ffffff` | `#0b0f16` / `#151a23` |
| `--warn` / `--danger` | status only (near-overdraft amber, overdraft red) | `#d97706` / `#dc2626` | `#e5a83b` / `#f07575` |

Type is Inter (via `next/font`) with tabular figures for money; 12–16px radii, hairline
borders, soft shadows; framer-motion springs on stream events, with a deliberate
grey-out treatment for the Orchestrator's **held/suppressed** moments.

## Compliance → law, in one paragraph

Per [`docs/05-legal-compliance.md`](docs/05-legal-compliance.md): the **consent-before-data
gate with granular per-mode opt-in, purpose statement and adult confirmation** implements
DPDP 2023 §5–6 (notice; free/specific/informed consent) and §9 (no minors); **withdraw
consent** (Settings + the always-visible real-data banner) is §6(4); **"What Ariagent knows"
with per-inference delete** and **Export/Delete my data** are the §11–12 access/correction/
erasure rights; the **audit log** (who/what/when/why/reversible, exportable) evidences RBI
outsourcing accountability; **statement upload instead of credentials** and the stubbed
**Account Aggregator** flow follow the RBI AA framework (no scraping, no credential
storage); and **analyse-only real mode + disclaimers on SIP/insurance cards + human-in-
the-loop approval** keep Ariagent outside SEBI RIA / IRDAI licensing and RBI-PSP scope
(and satisfy GDPR Art. 22 if it ever meets an EU user).

## Docs (the submission artifacts)

| # | Doc | Hackathon deliverable |
|---|---|---|
| 0 | [Locked decisions](docs/00-decisions-locked.md) | foundation / source of truth |
| 1 | [Idea description](docs/01-idea-description.md) | #3 Brief description of the idea |
| 2 | [Architecture & process flow](docs/02-architecture.md) | #6 Process flow / architecture |
| 3 | [Business model](docs/03-business-model.md) | #4 Business model / commercial potential |
| 4 | [Technology stack](docs/04-tech-stack.md) | #5 Technology stack details |
| 5 | [Legal & compliance](docs/05-legal-compliance.md) | #7 compliance review (binding on the build) |

## Repo map

```
backend/app
  agents/          Sentinel · Insight · Orchestrator · Engagement · Action
  detectors/       overdraft · duplicate_subscription · salary_hike · roundup · life_event_baby
  pipeline.py      the Sense→Reason→Decide→Act→Explain loop (SSE)
  statements.py    statement parsing, column-mapping detection, normalizer
  categorize.py    merchant→category: rules table + local-LLM fallback
  store.py         SQLite: consent, audit log, imported txns, inferences
  forecast.py      deterministic cashflow projection
  main.py          API: stream, consent, upload/import/mode, inferences, audit, export, delete
frontend/src
  app/             dashboard · onboarding · data · knowledge · audit · settings
  components/      agent-stream · action-card · cashflow-chart · timeline · upload-wizard · shell
  lib/             api client · types · app context (theme/status)
```
