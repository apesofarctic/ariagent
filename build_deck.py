#!/usr/bin/env python3
"""Generate the Ariagent idea-submission deck (PPTX).

Run: python3 build_deck.py  ->  Ariagent_Idea_Deck.pptx
Theme: dark slate + teal/amber accents, clean sans, 16:9.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---- palette ----
BG      = RGBColor(0x0E, 0x14, 0x1B)  # deep slate
CARD    = RGBColor(0x17, 0x20, 0x2B)  # card
INK     = RGBColor(0xF4, 0xF6, 0xF8)  # near-white
MUTE    = RGBColor(0x9A, 0xA7, 0xB4)  # muted grey
TEAL    = RGBColor(0x35, 0xD0, 0xBA)  # protect/primary accent
AMBER   = RGBColor(0xF2, 0xB1, 0x47)  # grow accent
VIOLET  = RGBColor(0x9B, 0x8C, 0xFF)  # guide accent
LINE    = RGBColor(0x2A, 0x36, 0x44)

W, H = Inches(13.333), Inches(7.5)
FONT = "Calibri"

prs = Presentation()
prs.slide_width = W
prs.slide_height = H
BLANK = prs.slide_layouts[6]


def slide():
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    r.fill.solid(); r.fill.fore_color.rgb = BG
    r.line.fill.background()
    r.shadow.inherit = False
    return s


def box(s, x, y, w, h, fill=None, line=None, line_w=1.0, radius=False):
    shp_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = s.shapes.add_shape(shp_type, x, y, w, h)
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def text(s, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         space_after=6, line_spacing=1.0):
    """runs: list of paragraphs; each paragraph is list of (txt, size, color, bold)."""
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        for (txt, size, color, bold) in para:
            r = p.add_run(); r.text = txt
            r.font.size = Pt(size); r.font.color.rgb = color
            r.font.bold = bold; r.font.name = FONT
    return tb


def chip(s, x, y, label, color):
    w = Inches(0.30 + 0.105 * len(label))
    box(s, x, y, w, Inches(0.34), fill=None, line=color, line_w=1.25, radius=True)
    tb = text(s, x, y, w, Inches(0.34), [[(label, 11, color, True)]],
              align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    tb.text_frame.word_wrap = False
    return x + w


def kicker(s, txt, color=TEAL):
    text(s, Inches(0.7), Inches(0.55), Inches(11), Inches(0.4),
         [[(txt.upper(), 13, color, True)]], space_after=0)


def title(s, txt, y=Inches(0.95), size=30):
    text(s, Inches(0.7), y, Inches(12), Inches(0.9),
         [[(txt, size, INK, True)]], space_after=0)


def footer(s, n):
    text(s, Inches(0.7), Inches(7.02), Inches(8), Inches(0.35),
         [[("Ariagent — Proactive Agentic Banking  ·  Digital Engagement", 9, MUTE, False)]],
         space_after=0)
    text(s, Inches(11.6), Inches(7.02), Inches(1.1), Inches(0.35),
         [[(f"{n:02d}", 9, MUTE, True)]], align=PP_ALIGN.RIGHT, space_after=0)


def bullet(s, x, y, w, items, dot=TEAL, size=14, gap=0.46):
    for i, (head, body) in enumerate(items):
        yy = y + Inches(gap * i)
        box(s, x, yy + Inches(0.07), Inches(0.12), Inches(0.12), fill=dot, radius=True)
        runs = [[(head, size, INK, True)] + ([(" — " + body, size, MUTE, False)] if body else [])]
        text(s, x + Inches(0.28), yy, w, Inches(0.5), runs, space_after=0, line_spacing=1.0)


# =========================================================================
# 1 — TITLE
# =========================================================================
s = slide()
box(s, 0, 0, Inches(0.18), H, fill=TEAL)
text(s, Inches(0.7), Inches(1.5), Inches(12), Inches(0.5),
     [[("ARIAGENT", 16, TEAL, True)]], space_after=0)
text(s, Inches(0.7), Inches(2.0), Inches(12), Inches(1.6),
     [[("The proactive financial companion", 46, INK, True)],
      [("that Protects, Grows, and Guides.", 46, INK, True)]],
     space_after=2, line_spacing=1.02)
text(s, Inches(0.7), Inches(3.95), Inches(11.5), Inches(0.8),
     [[("Most banking AI waits for you to ask. Ariagent watches your financial life and "
        "acts first — and shows you exactly why, every time.", 16, MUTE, False)]],
     line_spacing=1.1)
x = Inches(0.7)
x = chip(s, x, Inches(5.05), "PROTECT", TEAL) + Inches(0.15)
x = chip(s, x, Inches(5.05), "GROW", AMBER) + Inches(0.15)
x = chip(s, x, Inches(5.05), "GUIDE", VIOLET)
box(s, Inches(0.7), Inches(5.95), Inches(11.9), Pt(1.4), fill=LINE)
text(s, Inches(0.7), Inches(6.15), Inches(12), Inches(0.9),
     [[("Theme: Digital Engagement (Problem Statement #3)", 13, INK, True)],
      [("Project: Ariagent", 12, MUTE, False)]],
     space_after=4)

# =========================================================================
# 2 — PROBLEM
# =========================================================================
s = slide(); kicker(s, "The problem"); title(s, "Digital banking engagement is reactive — and shallow")
text(s, Inches(0.7), Inches(1.75), Inches(11.8), Inches(0.7),
     [[("Banks spend heavily on apps, yet the app is a destination the customer must choose to "
        "visit — and when they do, it only answers questions they already knew to ask.", 15, MUTE, False)]],
     line_spacing=1.12)
cards = [
    ("Harm goes uncaught", "Overdrafts, forgotten subscriptions and fraud are noticed after the money is gone.", TEAL),
    ("Opportunity is missed", "Idle balances and income changes sit unaddressed; the customer never gets ahead.", AMBER),
    ("Big moments unsupported", "A baby, a new home, a job change — the bank is silent because no one filled a form.", VIOLET),
]
cw = Inches(3.83); gap = Inches(0.2); x0 = Inches(0.7); y0 = Inches(2.75)
for i, (h, b, c) in enumerate(cards):
    cx = x0 + (cw + gap) * i
    box(s, cx, y0, cw, Inches(2.5), fill=CARD, radius=True)
    box(s, cx, y0, cw, Inches(0.12), fill=c, radius=True)
    text(s, cx + Inches(0.3), y0 + Inches(0.45), cw - Inches(0.6), Inches(0.6),
         [[(h, 18, INK, True)]], space_after=0)
    text(s, cx + Inches(0.3), y0 + Inches(1.15), cw - Inches(0.6), Inches(1.2),
         [[(b, 13.5, MUTE, False)]], line_spacing=1.12)
text(s, Inches(0.7), Inches(5.65), Inches(11.8), Inches(0.8),
     [[("Generic push notifications don't fix this — they're untimed, impersonal, and quickly muted. ", 15, MUTE, False),
       ("The missing capability is judgment.", 15, TEAL, True)]], line_spacing=1.1)
footer(s, 2)

# =========================================================================
# 3 — SOLUTION
# =========================================================================
s = slide(); kicker(s, "The idea"); title(s, "Ariagent — one agent engine, three engagement modes")
text(s, Inches(0.7), Inches(1.72), Inches(11.8), Inches(0.6),
     [[("A continuous agentic loop — ", 15, MUTE, False),
       ("Sense → Reason → Decide → Act → Explain", 15, INK, True),
       (" — run over three classes of signal.", 15, MUTE, False)]], line_spacing=1.1)
modes = [
    ("PROTECT", TEAL, "Threats", "Forecasts overdrafts, catches duplicate subscriptions & fraud — reaches out before harm.",
     "“Your rent debits before your salary lands — shift it?”"),
    ("GROW", AMBER, "Opportunities", "Detects idle cash and income changes — puts money to work.",
     "“Your salary rose ₹15k — auto-invest ₹5k/month?”"),
    ("GUIDE", VIOLET, "Life events", "Recognises life events from spending — orchestrates multi-step journeys.",
     "“A baby is coming — let's set up cover + savings, step by step.”"),
]
cw = Inches(3.83); x0 = Inches(0.7); y0 = Inches(2.5)
for i, (m, c, kind, body, quote) in enumerate(modes):
    cx = x0 + (cw + Inches(0.2)) * i
    box(s, cx, y0, cw, Inches(3.1), fill=CARD, radius=True)
    chip(s, cx + Inches(0.3), y0 + Inches(0.3), m, c)
    text(s, cx + Inches(0.3), y0 + Inches(0.85), cw - Inches(0.6), Inches(0.4),
         [[("Detects: " + kind, 12, MUTE, True)]], space_after=0)
    text(s, cx + Inches(0.3), y0 + Inches(1.3), cw - Inches(0.6), Inches(1.1),
         [[(body, 13.5, INK, False)]], line_spacing=1.12)
    box(s, cx + Inches(0.3), y0 + Inches(2.45), cw - Inches(0.6), Pt(1), fill=LINE)
    text(s, cx + Inches(0.3), y0 + Inches(2.55), cw - Inches(0.6), Inches(0.5),
         [[(quote, 11.5, c, False)]], line_spacing=1.05)
footer(s, 3)

# =========================================================================
# 4 — WHY AGENTIC
# =========================================================================
s = slide(); kicker(s, "Why it's genuinely agentic"); title(s, "Not a chatbot. Not a rules engine.")
items = [
    ("Autonomous & proactive", "It initiates — the customer doesn't. Engagement is a loop, not a notification feed."),
    ("Reasons & prioritises", "The Orchestrator decides which signal deserves attention now, holds back low-value nudges, "
                              "and interleaves slow journeys with urgent alerts. It will stay silent to avoid spam — that judgment is the product."),
    ("Accountable", "Every recommendation carries a visible reasoning trace, and every action is suitability-checked, "
                    "consented, reversible, and audited."),
]
box(s, Inches(0.7), Inches(1.9), Inches(7.4), Inches(4.5), fill=CARD, radius=True)
bullet(s, Inches(1.05), Inches(2.35), Inches(6.8), [(h, b) for h, b in items], dot=TEAL, size=15, gap=1.35)
# right panel: the loop
px = Inches(8.4); pw = Inches(4.2)
box(s, px, Inches(1.9), pw, Inches(4.5), fill=BG, line=LINE, line_w=1.2, radius=True)
text(s, px, Inches(2.1), pw, Inches(0.4), [[("THE LOOP", 12, MUTE, True)]], align=PP_ALIGN.CENTER, space_after=0)
loop = [("Sense", "Sentinel"), ("Reason", "Insight"), ("Decide", "Orchestrator"),
        ("Act", "Action"), ("Explain", "Engagement")]
for i, (step, agent) in enumerate(loop):
    yy = Inches(2.6 + 0.74 * i)
    box(s, px + Inches(0.4), yy, pw - Inches(0.8), Inches(0.58), fill=CARD, radius=True)
    text(s, px + Inches(0.65), yy, Inches(2), Inches(0.58),
         [[(step, 15, INK, True)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    text(s, px + Inches(1.9), yy, pw - Inches(2.3), Inches(0.58),
         [[(agent, 12, TEAL, True)]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.RIGHT, space_after=0)
footer(s, 4)

# =========================================================================
# 5 — ARCHITECTURE
# =========================================================================
s = slide(); kicker(s, "Process flow / architecture"); title(s, "Five agents, two pluggable libraries")
text(s, Inches(0.7), Inches(1.7), Inches(11.8), Inches(0.5),
     [[("One shared pipeline. Adding a mode = registering more detectors and actions — not a new system.", 14, MUTE, False)]],
     line_spacing=1.05)
stages = [
    ("SIGNALS", "txns · balances · recurring debits · merchants · goals", MUTE),
    ("SENTINEL", "Sense — runs detector library across all 3 modes → typed signals", TEAL),
    ("INSIGHT", "Reason — score relevance · urgency · confidence · intent", TEAL),
    ("ORCHESTRATOR", "Decide — prioritise · suppress spam · sequence journeys", AMBER),
    ("ENGAGEMENT + ACTION", "Explain the nudge + reasoning trace · execute guarded banking tools", VIOLET),
    ("GUARDRAILS", "suitability · consent · reversibility · full audit log", INK),
]
y = Inches(2.35); rh = Inches(0.66); rw = Inches(11.9)
for i, (h, b, c) in enumerate(stages):
    yy = y + (rh + Inches(0.12)) * i
    box(s, Inches(0.7), yy, rw, rh, fill=CARD, radius=True)
    box(s, Inches(0.7), yy, Inches(0.1), rh, fill=c, radius=True)
    text(s, Inches(1.0), yy, Inches(3.2), rh, [[(h, 14, INK, True)]],
         anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    text(s, Inches(4.2), yy, Inches(8.2), rh, [[(b, 12.5, MUTE, False)]],
         anchor=MSO_ANCHOR.MIDDLE, space_after=0)
footer(s, 5)

# =========================================================================
# 6 — DEMO
# =========================================================================
s = slide(); kicker(s, "The demo", VIOLET); title(s, "Priya, 29 — one 60-day timeline, all three modes")
text(s, Inches(0.7), Inches(1.7), Inches(11.8), Inches(0.5),
     [[("Just got a ₹15k raise — and her spending quietly reveals she's pregnant, before she'd ever fill a form.", 14, MUTE, False)]],
     line_spacing=1.05)
rows = [
    ("Day 3", "PROTECT", TEAL, "Rent debits before salary lands → overdraft forecast", "Shift the debit date (one tap)"),
    ("Day 8", "PROTECT", TEAL, "Two subscriptions for the same service", "Cancel the duplicate"),
    ("Day 14", "GROW", AMBER, "Salary +₹15k for 2 months, surplus idle", "Start a ₹5k/mo SIP"),
    ("Day 22", "GUIDE", VIOLET, "Prenatal-clinic pattern → baby life event", "Launch the “New Baby” journey"),
    ("Day 27", "ORCHESTRATOR", INK, "A low-value Grow nudge is suppressed (2 higher items pending)", "Nothing fires — shown in the log"),
]
y = Inches(2.4); rh = Inches(0.72)
for i, (day, mode, c, sig, act) in enumerate(rows):
    yy = y + (rh + Inches(0.1)) * i
    box(s, Inches(0.7), yy, Inches(11.9), rh, fill=CARD, radius=True)
    text(s, Inches(0.95), yy, Inches(1.1), rh, [[(day, 14, INK, True)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    chip(s, Inches(2.1), yy + Inches(0.19), mode, c)
    text(s, Inches(4.55), yy, Inches(4.7), rh, [[(sig, 12, MUTE, False)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0, line_spacing=1.0)
    text(s, Inches(9.35), yy, Inches(3.0), rh, [[("→ " + act, 12, c, True)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0, line_spacing=1.0)
footer(s, 6)

# =========================================================================
# 7 — DIFFERENTIATOR
# =========================================================================
s = slide(); kicker(s, "What makes it win"); title(s, "Judgment you can see")
diff = [
    ("Visible reasoning", "Every card shows its “why”: salary +₹15k × 2 months → ₹9k recurring surplus → SIP. Trust the black box can't earn.", TEAL),
    ("Restraint (anti-spam)", "The Orchestrator deliberately suppresses lower-value nudges. A rule engine fires on every match — an agent decides not to.", AMBER),
    ("Compliance by design", "Suitability, consent, reversibility and audit are built in — the credibility a regulated domain demands.", VIOLET),
]
cw = Inches(3.83); x0 = Inches(0.7); y0 = Inches(2.1)
for i, (h, b, c) in enumerate(diff):
    cx = x0 + (cw + Inches(0.2)) * i
    box(s, cx, y0, cw, Inches(3.0), fill=CARD, radius=True)
    box(s, cx, y0, cw, Inches(0.12), fill=c, radius=True)
    text(s, cx + Inches(0.3), y0 + Inches(0.45), cw - Inches(0.6), Inches(0.7),
         [[(h, 18, INK, True)]], space_after=0, line_spacing=1.0)
    text(s, cx + Inches(0.3), y0 + Inches(1.35), cw - Inches(0.6), Inches(1.5),
         [[(b, 13.5, MUTE, False)]], line_spacing=1.15)
text(s, Inches(0.7), Inches(5.5), Inches(11.9), Inches(0.9),
     [[("The money shot for judges: ", 15, INK, True),
       ("watching the agents reason in real time — and the Day-27 moment where Ariagent chooses to stay silent.", 15, MUTE, False)]],
     line_spacing=1.1)
footer(s, 7)

# =========================================================================
# 8 — BUSINESS MODEL
# =========================================================================
s = slide(); kicker(s, "Business model / commercial potential"); title(s, "Every mode is a revenue lever")
rows = [
    ("PROTECT", TEAL, "Retention + NII + lower servicing", "Buffer credit / overdraft lines · fewer NSF complaints · churn ↓"),
    ("GROW", AMBER, "AUM + fee income + deposit stickiness", "SIPs · mutual funds · high-yield sweeps"),
    ("GUIDE", VIOLET, "Cross-sell bundles (highest ₹/event)", "Insurance + investment + savings, sold at the moment of need"),
]
y = Inches(2.0); rh = Inches(0.92)
for i, (m, c, lever, ex) in enumerate(rows):
    yy = y + (rh + Inches(0.14)) * i
    box(s, Inches(0.7), yy, Inches(11.9), rh, fill=CARD, radius=True)
    chip(s, Inches(0.95), yy + Inches(0.29), m, c)
    text(s, Inches(3.4), yy, Inches(4.2), rh, [[(lever, 14.5, INK, True)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    text(s, Inches(7.7), yy, Inches(4.7), rh, [[(ex, 12.5, MUTE, False)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0, line_spacing=1.05)
box(s, Inches(0.7), Inches(5.5), Inches(11.9), Inches(1.05), fill=BG, line=TEAL, line_w=1.3, radius=True)
text(s, Inches(1.0), Inches(5.6), Inches(11.3), Inches(0.9),
     [[("Platform multiplier: ", 14, TEAL, True),
       ("the same engine powers Customer Acquisition (#1) and Digital Adoption (#2) — one architecture answers all three problem statements. "
        "Sold B2B2C to banks (per-active-user) + cost-avoidance, expanding to revenue-share.", 13, INK, False)]],
     anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)
footer(s, 8)

# =========================================================================
# 9 — METRICS
# =========================================================================
s = slide(); kicker(s, "How we measure success"); title(s, "One north star, balanced against spam")
box(s, Inches(0.7), Inches(2.0), Inches(5.7), Inches(1.4), fill=CARD, radius=True)
box(s, Inches(0.7), Inches(2.0), Inches(0.12), Inches(1.4), fill=TEAL, radius=True)
text(s, Inches(1.0), Inches(2.18), Inches(5.2), Inches(0.5), [[("NORTH STAR", 12, TEAL, True)]], space_after=0)
text(s, Inches(1.0), Inches(2.55), Inches(5.2), Inches(0.8),
     [[("Proactive Actions Accepted / active user / month", 17, INK, True)]], line_spacing=1.0, space_after=0)
box(s, Inches(6.6), Inches(2.0), Inches(6.0), Inches(1.4), fill=CARD, radius=True)
box(s, Inches(6.6), Inches(2.0), Inches(0.12), Inches(1.4), fill=AMBER, radius=True)
text(s, Inches(6.9), Inches(2.18), Inches(5.5), Inches(0.5), [[("GUARDRAIL METRIC", 12, AMBER, True)]], space_after=0)
text(s, Inches(6.9), Inches(2.55), Inches(5.5), Inches(0.8),
     [[("Nudge acceptance rate ↑  &  opt-out rate ↓", 17, INK, True)]], line_spacing=1.0, space_after=0)
drivers = [
    ("PROTECT drivers", "overdrafts avoided · fraud caught · ₹ saved · churn ↓", TEAL),
    ("GROW drivers", "surplus activated (₹ moved to productive) · SIPs started · AUM ↑", AMBER),
    ("GUIDE drivers", "journeys started → completed · products per journey · cross-sell ratio ↑", VIOLET),
]
y = Inches(3.75)
for i, (h, b, c) in enumerate(drivers):
    yy = y + Inches(0.78) * i
    box(s, Inches(0.7), yy, Inches(11.9), Inches(0.64), fill=CARD, radius=True)
    box(s, Inches(0.7), yy, Inches(0.1), Inches(0.64), fill=c, radius=True)
    text(s, Inches(1.0), yy, Inches(3.2), Inches(0.64), [[(h, 13.5, INK, True)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    text(s, Inches(4.2), yy, Inches(8.2), Inches(0.64), [[(b, 12.5, MUTE, False)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0)
footer(s, 9)

# =========================================================================
# 10 — TECH STACK
# =========================================================================
s = slide(); kicker(s, "Technology stack"); title(s, "Privacy-first, runs on no budget")
layers = [
    ("Frontend", "Next.js + React + Tailwind — live dashboard: timeline, action cards, streaming reasoning traces", TEAL),
    ("Backend", "Python FastAPI — agent pipeline, signal bus, audit log; SSE streams reasoning to the UI", TEAL),
    ("Agent engine", "Ollama + Qwen2.5 (local, free, private) · provider-agnostic — one-line swap to a hosted model", AMBER),
    ("Data", "Synthetic transaction generator (the Priya scenario) · SQLite → Postgres", VIOLET),
    ("Guardrails", "Cross-cutting compliance: suitability · consent · reversibility · audit", INK),
]
y = Inches(1.95); rh = Inches(0.66)
for i, (h, b, c) in enumerate(layers):
    yy = y + (rh + Inches(0.12)) * i
    box(s, Inches(0.7), yy, Inches(11.9), rh, fill=CARD, radius=True)
    box(s, Inches(0.7), yy, Inches(0.1), rh, fill=c, radius=True)
    text(s, Inches(1.0), yy, Inches(2.6), rh, [[(h, 14, INK, True)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    text(s, Inches(3.6), yy, Inches(8.8), rh, [[(b, 12.5, MUTE, False)]], anchor=MSO_ANCHOR.MIDDLE, space_after=0)
box(s, Inches(0.7), Inches(5.95), Inches(11.9), Inches(0.75), fill=BG, line=TEAL, line_w=1.3, radius=True)
text(s, Inches(1.0), Inches(5.95), Inches(11.3), Inches(0.75),
     [[("Hybrid by design: ", 13.5, TEAL, True),
       ("forecasting & suppression thresholds run as deterministic code — the model handles language & classification. "
        "Financial data never leaves the host; the same stack runs in a bank's own VPC.", 12.5, INK, False)]],
     anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.08)
footer(s, 10)

# =========================================================================
# 11 — ROADMAP / TRUST LADDER
# =========================================================================
s = slide(); kicker(s, "Roadmap — earning autonomy"); title(s, "The trust ladder")
text(s, Inches(0.7), Inches(1.7), Inches(11.8), Inches(0.5),
     [[("Autonomy in a regulated domain is earned in stages, not switched on.", 14, MUTE, False)]], line_spacing=1.0)
tiers = [
    ("TIER 1 — Suggest", "Ariagent recommends; you approve in one tap.", "Today's demo", TEAL),
    ("TIER 2 — Standing rules", "Pre-authorise a class of action within limits (“always shift my debit if I'd overdraft”).", "Next", AMBER),
    ("TIER 3 — Pulse (autopilot)", "Full delegation; Ariagent manages idle money continuously + a weekly “what I did & why” explainer.", "Vision", VIOLET),
]
y = Inches(2.45); rh = Inches(1.2)
for i, (h, b, tag, c) in enumerate(tiers):
    yy = y + (rh + Inches(0.18)) * i
    box(s, Inches(0.7), yy, Inches(11.9), rh, fill=CARD, radius=True)
    box(s, Inches(0.7), yy, Inches(0.14), rh, fill=c, radius=True)
    text(s, Inches(1.1), yy + Inches(0.2), Inches(7.4), Inches(0.5), [[(h, 17, INK, True)]], space_after=0)
    text(s, Inches(1.1), yy + Inches(0.66), Inches(8.8), Inches(0.5), [[(b, 13, MUTE, False)]], space_after=0, line_spacing=1.0)
    chip(s, Inches(10.9), yy + Inches(0.44), tag, c)
footer(s, 11)

# =========================================================================
# 12 — CLOSE
# =========================================================================
s = slide()
box(s, 0, 0, Inches(0.18), H, fill=TEAL)
text(s, Inches(0.7), Inches(1.6), Inches(12), Inches(0.5), [[("ARIAGENT", 16, TEAL, True)]], space_after=0)
text(s, Inches(0.7), Inches(2.15), Inches(12), Inches(2.0),
     [[("Engagement becomes something the", 38, INK, True)],
      [("bank ", 38, INK, True), ("does for", 38, TEAL, True), (" the customer —", 38, INK, True)],
      [("not something it sells.", 38, INK, True)]], space_after=2, line_spacing=1.03)
text(s, Inches(0.7), Inches(4.7), Inches(11.8), Inches(0.9),
     [[("Protects, Grows, and Guides on one agent engine · suggests today, earns autopilot tomorrow · "
        "proves its trustworthiness by showing its reasoning on every action.", 15, MUTE, False)]],
     line_spacing=1.15)
box(s, Inches(0.7), Inches(5.95), Inches(11.9), Pt(1.4), fill=LINE)
x = Inches(0.7)
x = chip(s, x, Inches(6.2), "PROTECT", TEAL) + Inches(0.15)
x = chip(s, x, Inches(6.2), "GROW", AMBER) + Inches(0.15)
x = chip(s, x, Inches(6.2), "GUIDE", VIOLET)
text(s, Inches(9.3), Inches(6.2), Inches(3.3), Inches(0.4),
     [[("Digital Engagement · #3", 12, MUTE, True)]], align=PP_ALIGN.RIGHT, space_after=0)

out = "Ariagent_Idea_Deck.pptx"
prs.save(out)
print("saved", out, "·", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
