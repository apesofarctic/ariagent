# Ariagent — Legal & Data-Compliance Review (Deliverable #7)

> Scope: what personal/financial data Ariagent touches, which laws apply (India-first, since the
> anchor context is SBI / Indian retail banking), and the **concrete product/UI requirements** that
> flow from those laws. Split into (A) what the **prototype** must show to be credible, and (B) what
> **production** must actually implement. The design and the Fable 5 build prompt both reference this doc.

---

## 0. TL;DR — the compliance posture (the "analysis-only companion" doctrine)

The entire legal risk of a "financial agent" comes from **doing things to people's accounts** — pulling
data from banks, giving licensed advice, moving money. Ariagent avoids all of it with one positioning
decision:

> **Ariagent is a read-only, on-device financial *analyst*, not a financial-services provider. The user
> brings their own data, Ariagent does the thinking, the user stays in control of every action.**

That framing places Ariagent in the same lightly-regulated category as a budgeting / money-manager app:
DPDP applies for data handling, but there is **no SEBI / IRDAI / RBI licensing trigger**. It is
also **privacy-first by construction** — all inference is local (Ollama + Qwen2.5 on the host), so raw
financial data never leaves the machine. Four things must be true regardless of where the model runs:

1. **Import, don't integrate.** Real data enters only by the user **uploading their own bank statement**
   (BYO data) or, in production, via the RBI **Account Aggregator** rail — never by scraping, storing
   credentials, or pulling from banks directly.
2. **Consent before data, always.** No transaction is ingested and no signal computed until the user has
   given free, specific, informed, revocable consent — with a stated purpose.
3. **Analyse & suggest — never advise or execute.** Surfacing *facts* about the user's own money
   ("you have ₹9k recurring surplus") is not regulated advice. Recommending a specific SIP (SEBI) or
   insurance (IRDAI), or moving money (RBI/PSP), is. The prototype surfaces facts and generic options,
   frames actions as *"prepare an instruction the user executes in their own bank app,"* carries
   disclaimers, and **never executes** anything itself.
4. **Data rights are first-class.** The user can see everything Ariagent knows, export it, and delete
   it. These are legal rights under DPDP 2023, not nice-to-haves.

---

## 1. Data inventory — what the agent actually touches

| Data element | Sensitivity | Source in Ariagent | Notes |
|---|---|---|---|
| Transactions (date, amount, merchant, category) | **High** — financial | synthetic gen / CSV upload / Account Aggregator | Core input. Merchant+category can reveal health, religion, sexuality (a pharmacy pattern = pregnancy — literally the demo). |
| Account balance | High | profile / statement | Used for overdraft forecast. |
| Recurring debits (rent, salary, subscriptions) | High | derived / profile | Reveals employer, landlord, income. |
| Derived life-event inferences (baby, new job, relocation) | **Very high** — special-category-adjacent | Insight/Sentinel agents | Inferred *health/family* data. Legally the most dangerous output — treat as sensitive. |
| Name / customer id | Medium (PII) | profile | Minimise; a pseudonymous id is enough for the engine. |
| Consent record + audit log | — | guardrail layer | Itself must be retained as compliance evidence. |

**Key point:** even though every field looks like "just a bank transaction," the *inferences* Ariagent
draws (pregnancy, job loss, health spend) are the sensitive part. Indian and EU law both treat
inferred health/family data as protected. This is the demo's superpower and its biggest liability.

---

## 2. Applicable law (India-first)

### 2.1 DPDP Act 2023 (Digital Personal Data Protection Act) — the primary law
Ariagent is a **Data Fiduciary**; the customer is the **Data Principal**. Obligations that map to product features:

- **Consent (§6):** must be *free, specific, informed, unconditional, unambiguous, with clear
  affirmative action*, and tied to a **stated purpose**. Bundled/blanket consent is invalid.
  → *Product:* a consent screen that names the purpose ("watch your transactions to warn you of
  overdrafts, find savings, and guide life events") with an explicit opt-in per data use.
- **Notice (§5):** plain-language notice of what is collected and why, at/ before consent.
- **Purpose limitation & data minimisation (§6, §8):** collect only what the purpose needs; don't
  repurpose. → Ariagent should not need full account numbers, only transaction rows.
- **Right to access, correction, erasure (§11–12):** the Principal can see, fix, and delete their data.
  → *Product:* "Export my data" and "Delete everything" must exist and work.
- **Right to withdraw consent (§6(4)):** as easy to withdraw as to give. → a visible toggle, and
  withdrawal stops processing going forward.
- **Consent Manager:** DPDP recognises registered Consent Managers — the RBI **Account Aggregator**
  network is the practical consent rail for financial data (see 2.2).
- **Security safeguards & breach notification (§8):** reasonable security; report breaches to the
  Data Protection Board and affected principals.
- **Children (§9):** no behavioural monitoring / targeted processing of minors. → Ariagent must gate
  to adult account holders.

### 2.2 RBI Account Aggregator (AA) framework — the *only* sanctioned rail for real bank data
To pull a customer's **real** transaction data programmatically in India, you go through an RBI-licensed
Account Aggregator (Finvu, OneMoney, Setu/Anumati, CAMS Finserv, etc.), not by scraping or asking for
net-banking passwords. Properties:
- **Consent artefact:** machine-readable, time-bound, purpose-bound, revocable. Specifies FI types,
  data range, frequency, and consent duration.
- **Data flow:** FIP (bank) → AA → FIU (Ariagent), encrypted end-to-end; AA cannot read the data.
- → *Product:* the "connect real data" path should be modelled as an **AA consent flow** (even if the
  prototype stubs it). Manual **statement/CSV upload** is the compliant no-integration fallback — the
  user voluntarily provides their own data.

### 2.3 SEBI — investment advice (the `start_sip` / `sweep_to_high_yield` actions)
Giving **personalised investment advice** for consideration requires SEBI **Registered Investment
Adviser (RIA)** registration; recommending/distributing mutual funds requires being an AMFI-registered
distributor. Ariagent (or a hackathon prototype) is neither.
→ *Rules:* (a) never present SIP/investment suggestions as independent advice; frame as
"the bank can set this up for you" / execution-only, suitability-checked, with a **"not investment
advice"** disclaimer; (b) in production this action is performed by the **bank's licensed entity**,
Ariagent only surfaces the suggestion. This is exactly why the guardrail layer enforces *suitability +
consent + reversibility + human-approved (Tier 1)*.

### 2.4 IRDAI — insurance (the `buy_insurance` action)
Soliciting/recommending insurance requires an IRDAI intermediary licence (agent/broker/corporate agent).
→ Same treatment as SEBI: Ariagent *suggests a review*; the licensed bank/insurer executes. Disclaimer
required. Keep out of the MVP execution path — surface as a "review your cover" prompt only.

### 2.5 RBI — money movement, outsourcing, customer protection
- Moving money (`move_money`, `shift_debit_date`) is a regulated **payment** activity — only banks/PSPs
  may do it. The prototype uses **mock banking tools** (no real rails), which is the correct posture.
- **RBI outsourcing / (Digital Lending) directions:** when a bank uses a third-party agent, the *bank*
  remains liable; the agent must be auditable and consent-scoped. Ariagent's audit log is the evidence.
- **Payments data localisation (RBI, 2018):** payment data must be stored in India. Local-first
  inference and India-hosted storage satisfy this by design.

### 2.6 IT Act 2000 + SPDI Rules 2011 (still live alongside DPDP)
Financial information is **Sensitive Personal Data or Information (SPDI)** → requires a published privacy
policy, consent for collection, and **reasonable security practices** (ISO/IEC 27001 is the safe harbour).

### 2.7 If the demo/data ever touches EU/UK persons — GDPR
Then: lawful basis (consent/contract), **Art. 22** (no solely-automated decisions with legal/significant
effect without safeguards → keep the human-in-the-loop Tier-1 approval), **Art. 9** (health/family
inferences are special-category → explicit consent), DPIA required for this kind of profiling. The
Tier-1 "user approves in one tap" design already satisfies the Art. 22 human-oversight requirement — say
so in the pitch.

---

## 3. The two data modes (maps directly to the product requirement)

The product needs **(a)** a way to load *dummy* data to test the model, and **(b)** an option to
**import the user's real data** to run the analysis on. These have different compliance treatment and the
UI must make the difference obvious.

### Mode A — Demo / Sandbox data (default, zero-risk)
- Source: the built-in synthetic 60-day "Priya" generator, **or** a CSV the user uploads that is
  explicitly treated as test data.
- Compliance: **none triggered** — no real person's data. Clearly label the workspace **"DEMO DATA —
  not real, nothing is stored or acted on for real."**
- Purpose: exercise the agent loop, tune detectors, screenshots, judging.

### Mode B — Import real data for analysis (gated, consent-first)
This is the "run it on my actual money" path. Stay legal by staying **read-only + on-device + BYO data**.
- Source (in order of compliance-friendliness):
  1. **User-uploaded bank statement (BYO data)** — the user exports their *own* statement (CSV / Excel /
     PDF) from their bank and uploads it. They are voluntarily providing their own data → the cleanest
     path, **no integration, no licence.** This is the prototype's real-data path. Impact is undiminished:
     3–6 months of a real statement *is* the transaction stream the detectors need — you demonstrate the
     engine on the user's / judge's own real numbers.
  2. **Account Aggregator consent flow** (production only) — the RBI-sanctioned programmatic rail;
     requires being a registered FIU or partnering with a TSP (Setu/Finvu/…). **Stub** the consent-artefact
     screen in the prototype and label it "AA — coming soon."
- **Never** ask for net-banking credentials/OTPs, never scrape, never store full card/account numbers.
- **Import pipeline (practical):** real statements have no clean `category` column and every bank's export
  is shaped differently. So Mode B needs (i) a **normalizer** mapping the bank's columns → the
  `Transaction` schema, with a manual column-mapping fallback for unknown formats, and (ii) a
  **categorizer** (merchant → category) — a legitimate use of the local model for classification, backed
  by a rules table. All of this runs **on-device**.
- Gate: **cannot enter Mode B without passing the consent screen** (purpose + explicit opt-in + adult
  confirmation). Show a persistent "REAL DATA — consented on {date}, processed on-device" banner and a
  one-click "Revoke & delete."
- **Analyse-only:** Mode B produces insights and *prepared* actions (a ready-to-execute instruction / deep
  link the user completes in their own bank app). Nothing auto-executes; mock tools make clear no real
  money moves in the prototype. This is what keeps it out of SEBI/IRDAI/RBI-PSP scope.

> **Export & delete (DPDP rights, not the headline).** Independently of import, the user can **export**
> everything Ariagent holds (transactions + inferences + audit log as JSON/CSV) and **delete** it. Build
> both — they are required data-portability / erasure rights, but the star of Mode B is *import*.

---

## 4. Concrete product/UI requirements (what the build must include)

These are the compliance features Fable 5 must render — they are also a *pitch asset* (they show the
"regulated-domain credibility" the judges reward):

1. **Consent & onboarding screen** — plain-language purpose, granular opt-in (Protect / Grow / Guide can
   be toggled independently), adult confirmation, link to a privacy notice. No data flows before this.
2. **Data source panel** — clear switch between **Demo data** and **Real data**, with the labels/banners
   from §3. Upload-CSV and "connect via Account Aggregator (stub)".
3. **"What Ariagent knows about me" view** — every inference (esp. life-event inferences) shown in plain
   language, with the evidence trace and a **"this is wrong / delete"** control per inference. (Right to
   correction + transparency.)
4. **Export my data / Delete my data** — one click each. Export = JSON+CSV of transactions, signals,
   insights, decisions, actions, audit log. Delete = wipe + confirmation.
5. **Consent status + revoke** — always-visible; revoke stops processing and offers delete.
6. **Disclaimers on regulated actions** — SIP/insurance/money-move cards carry: *"Suggestion only. Not
   investment/insurance advice. Your bank executes this, subject to suitability. Reversible."*
7. **Audit log** — every action with who/what/when/**why**, reversibility flag. This is both a legal
   requirement (RBI outsourcing accountability) and the product's differentiator.
8. **Human-in-the-loop by default (Tier 1)** — nothing auto-executes in the prototype; every action is
   one-tap-approved. (Satisfies GDPR Art. 22 / responsible-AI framing.)

---

## 5. Red lines (do NOT do, in prototype or pitch)

- ❌ Don't claim Ariagent gives investment or insurance **advice** — it *surfaces suggestions the
  licensed bank executes*. (SEBI/IRDAI.)
- ❌ Don't ask for or store net-banking credentials / OTPs / full card numbers — use AA or user-uploaded
  statements only. (RBI/DPDP minimisation.)
- ❌ Don't move real money or connect real rails in the prototype — mock tools only.
- ❌ Don't process data before consent, and don't bundle consent into a single "I agree to everything."
- ❌ Don't send financial data to a hosted LLM without disclosing it — the local-model default is the
  privacy story; if a hosted provider is ever used, it must be consented and disclosed.

---

## 6. One-liner for the deck (the compliance slide)

> *Ariagent is privacy-first by construction (local inference, data never leaves the host), consent-first
> by design (DPDP-aligned granular consent, Account-Aggregator-ready), and accountable by default (every
> action suitability-checked, reversible, human-approved, and audited). Regulated actions are surfaced,
> not performed — the licensed bank executes them.*
