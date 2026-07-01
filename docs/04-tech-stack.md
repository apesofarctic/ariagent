# Ariagent — Technology Stack Details (Deliverable #5)

> Stack committed: **Next.js + FastAPI + local open-model agents (Ollama + Qwen2.5), provider-agnostic**. Privacy-first by design — financial data never leaves the host. Two versions below: a **paste-ready version** for the form box, and the **full justification** (per layer + why) for the deck and engineering plan.

---

## A. Paste-ready version (drop into form field #5)

**Frontend:** Next.js (React) + TailwindCSS + shadcn/ui — a real-time dashboard showing the customer timeline, proactive action cards, and live agent reasoning traces. Framer Motion for the agent-activity animations.

**Backend:** Python FastAPI — exposes the agent pipeline, the signal bus, and the audit log; async endpoints + WebSocket/SSE for streaming agent reasoning to the UI.

**Agent / AI layer:** Local open-model agents — **Ollama** running **Qwen2.5-Instruct** (7B default; 3B on low-spec, 14B where hardware allows), via Ollama's OpenAI-compatible API, using **tool-use (function calling)** for the agentic loop. Five cooperating agents — Sentinel, Insight, Orchestrator, Engagement, Action — orchestrated by a thin Python layer. The Action agent calls guarded "banking tools" (move_money, shift_debit_date, start_sip, cancel_subscription, etc.). The model layer is **provider-agnostic**: the same code targets a hosted model (Claude, GPT, Gemini) by changing one base-URL/key config — so the prototype runs free and fully private locally, and a bank can later point it at a self-hosted open model inside its own VPC.

**Why local-first:** zero API cost (built on no budget) **and** financial data never leaves the host — a genuine data-residency strength for banking, not just a cost hack. Correctness-critical logic (overdraft forecasting, suppression thresholds) runs as deterministic code, so a small local model is only responsible for language and classification, where 7B-class models are reliable.

**Data:** A synthetic transaction-stream generator seeds the demo (the 60-day "Priya" scenario with planted signals). Persistence via SQLite (prototype) / Postgres (production-shaped). In-memory event bus for signals.

**Guardrails:** A cross-cutting compliance layer — suitability checks, consent scope, reversibility, and a full audit log on every action.

**Demo resilience:** Runs fully offline on the local model (venue-wifi safe by construction); a scripted deterministic fallback guarantees the key demo beats even if the model wobbles.

**Deployment:** Vercel (frontend) + a container for the FastAPI backend (Render/Fly/Railway); Ollama runs on the host/judging machine. Local `docker-compose` for judging.

---

## B. Full justification (deck + engineering plan)

### Layer-by-layer

| Layer | Choice | Why this, for *this* product |
|---|---|---|
| **Frontend** | Next.js + React + Tailwind + shadcn/ui | The demo's "wow" is *visible* — timeline, action cards, and streaming reasoning traces. React gives a productized, judge-impressing UI; shadcn/ui ships clean components fast; Tailwind keeps styling velocity high. |
| **Realtime** | WebSocket / Server-Sent Events | Agent reasoning must *stream* into the UI as it happens (Sentinel → Insight → Orchestrator firing live). SSE is the lightweight fit for one-directional agent-event streaming. |
| **Animation** | Framer Motion | The agent-activity feed and the Day-27 suppression moment land better with motion. Cheap polish, high perceived sophistication. |
| **Backend** | FastAPI (Python) | Python is the lingua franca of agent/LLM work; FastAPI is async-native (needed for concurrent agent calls + streaming), typed (Pydantic models map cleanly to our Signal/Insight/Decision schema), and fast to build. |
| **Agent engine** | Ollama + Qwen2.5-Instruct (local), tool-use; provider-agnostic | The agentic loop *is* tool-use: agents reason, then call tools. Qwen2.5 is the strongest small open model for function-calling and runs locally for free. Provider-agnostic client means a hosted model (Claude/GPT/Gemini) is a one-line config swap. Bigger local model (14B) for the Orchestrator's judgment if hardware allows; 7B for high-frequency detectors/engagement. |
| **Privacy / cost** | Local inference (Ollama) | Zero marginal cost and data never leaves the host — a real data-residency advantage in a regulated domain. The same architecture runs on a bank's self-hosted open model inside its VPC. |
| **Orchestration** | Thin Python layer (no heavy framework) | A lightweight custom orchestrator keeps the five-agent pipeline legible and debuggable for a prototype, and keeps the "Orchestrator agent" logic explicit rather than hidden inside a framework. (LangGraph is a viable swap if graph-state grows.) |
| **Data / store** | Synthetic generator + SQLite (→ Postgres) | No real bank data needed for the demo; the generator gives a controllable, reproducible scenario with planted signals. SQLite is zero-setup for judging; the schema is Postgres-shaped for a credible "production path." |
| **Event bus** | In-memory pub/sub (prototype) | Signals flow Sentinel → Insight → Orchestrator as events. In-memory is enough for the demo; maps to Kafka/SQS in production (mention in roadmap). |
| **Guardrails** | Custom compliance middleware | Every Action passes through suitability + consent + reversibility + audit. This is the credibility layer for a regulated domain — built in, not bolted on. |
| **Deploy** | Vercel + container backend; docker-compose local | One-command local run for judges; cloud links for the submission. |

### Model strategy (cost / latency / privacy aware)
- **All inference is local by default** via Ollama — free and private. Sizing: `qwen2.5:7b` is the default; `qwen2.5:3b` on low-spec machines; `qwen2.5:14b` for richer Orchestrator reasoning where hardware allows.
- **Orchestrator** (low-frequency, high-stakes judgment) → the largest local model the machine can run.
- **Detectors / Insight / Engagement** (higher-frequency) → 7B for speed.
- Detectors that are pure arithmetic (e.g., overdraft forecast) run as **deterministic code**, not LLM calls — the LLM is used for *judgment and language*, not math. (This is both a cost and a correctness decision worth calling out: you don't ask an LLM to add up a balance — and it's what lets a small local model carry the demo.)
- **Provider-agnostic escape hatch:** point the client at a hosted model (Claude `claude-opus-4-8` / GPT / Gemini) by changing a base URL + key — useful if the venue provides API credits or for a higher-fidelity recorded demo. No code change beyond config.

### Why local open-model first (shows decision-making)
- **Free + private, by design** → no budget required, and customer financial data never leaves the host. In banking that's a data-residency *feature*, not a compromise — and it generalizes to a bank running the same stack in its own VPC.
- **Not a free hosted tier** (Groq / Gemini free / OpenRouter) → those are free but **not private** (data leaves your machine). Privacy was the requirement, so local wins.
- **Not a single monolithic prompt** → loses the multi-agent separation of concerns and the visible per-agent reasoning that *is* the demo.
- **Not Streamlit** → faster to build but reads as a prototype, not a product; the dashboard polish is part of the pitch.
- **Not "LLM decides everything"** → forecasting and suppression thresholds are deterministic where correctness matters; the local LLM handles ambiguity, classification, and language. This hybrid is what makes a small local model demo-reliable, and it's the responsible-engineering signal.

### Production-path note (one line for judges)
The prototype's in-memory bus → Kafka, SQLite → Postgres, synthetic feed → real core-banking/UPI/account-aggregator integrations, and local Ollama → the bank's own self-hosted open model inside its VPC; the agent pipeline and guardrail layer stay unchanged. The architecture is prototype-honest, privacy-first, and production-shaped.
