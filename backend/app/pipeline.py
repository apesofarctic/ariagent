import asyncio
from .agents.sentinel import Sentinel
from .agents.insight import InsightAgent
from .agents.orchestrator import Orchestrator
from .agents.engagement import Engagement
from .agents.action import ActionAgent
from . import store

_INFERENCE_TITLES = {
    "overdraft_forecast": "Your rent may bounce this month",
    "duplicate_subscription": "You're paying twice for the same service",
    "salary_hike": "Your salary went up recently",
    "life_event_baby": "There may be a little one on the way",
    "roundup_potential": "Your everyday spend has round-up potential",
}


async def run_pipeline(txns, profile, auto_approve: bool = True,
                       consented_modes: set[str] | None = None,
                       prepare_only: bool = False,
                       record: bool = False,
                       skip_types: set[str] | None = None):
    sentinel, insight, orch, eng, action = (
        Sentinel(), InsightAgent(), Orchestrator(), Engagement(), ActionAgent())

    yield {"stage": "sense", "agent": "Sentinel", "detail": "Scanning financial signals..."}
    signals = sentinel.sense(txns, profile, consented_modes=consented_modes,
                             skip_types=skip_types)
    yield {"stage": "sense", "agent": "Sentinel",
           "detail": f"{len(signals)} signal(s) detected",
           "signals": [s.model_dump() for s in signals]}

    insights = []
    for s in signals:
        await asyncio.sleep(0.3)
        ins = insight.reason(s, profile)
        insights.append(ins)
        if record:
            store.upsert_inference(
                s.type, s.mode, _INFERENCE_TITLES.get(s.type, s.type.replace("_", " ")),
                ins.why, s.evidence, s.confidence)
        yield {"stage": "reason", "agent": "Insight", "detail": ins.why,
               "signal": s.type, "mode": s.mode,
               "urgency": ins.urgency, "ev": ins.expected_value}

    for d in orch.decide(insights):
        sig = d.insight.signal
        yield {"stage": "decide", "agent": "Orchestrator",
               "detail": f"{d.action.upper()} — {d.reason}",
               "signal": sig.type, "mode": sig.mode, "action": d.action}
        if record and d.action in ("hold", "suppress"):
            verb = "held for later" if d.action == "hold" else "suppressed"
            store.audit("Orchestrator", d.action,
                        f"'{sig.type.replace('_', ' ')}' nudge {verb}",
                        d.reason, True, sig.mode,
                        "held" if d.action == "hold" else "suppressed")
        if d.action != "fire":
            continue
        await asyncio.sleep(0.3)
        nudge = eng.explain(d)
        yield {"stage": "explain", "agent": "Engagement", "detail": nudge.message,
               "mode": sig.mode, "signal": sig.type, "nudge": nudge.model_dump()}
        if auto_approve:
            res = action.act(nudge, profile, prepare_only=prepare_only)
            if record:
                status = ("prepared" if res.get("prepared")
                          else "executed" if res.get("executed") else "blocked")
                store.audit("Action", nudge.tool, res.get("result") or res.get("reason", ""),
                            d.insight.why, nudge.reversible, sig.mode, status)
            yield {"stage": "act", "agent": "Action",
                   "detail": res.get("result") or res.get("reason"),
                   "executed": res.get("executed", False),
                   "prepared": res.get("prepared", False),
                   "deep_link": res.get("deep_link"),
                   "tool": nudge.tool, "mode": sig.mode, "signal": sig.type}

    yield {"stage": "done", "agent": "System", "detail": "Pipeline complete"}
