import asyncio
from .agents.sentinel import Sentinel
from .agents.insight import InsightAgent
from .agents.orchestrator import Orchestrator
from .agents.engagement import Engagement
from .agents.action import ActionAgent


async def run_pipeline(txns, profile, auto_approve: bool = True):
    sentinel, insight, orch, eng, action = (
        Sentinel(), InsightAgent(), Orchestrator(), Engagement(), ActionAgent())

    yield {"stage": "sense", "agent": "Sentinel", "detail": "Scanning financial signals..."}
    signals = sentinel.sense(txns, profile)
    yield {"stage": "sense", "agent": "Sentinel",
           "detail": f"{len(signals)} signal(s) detected",
           "signals": [s.model_dump() for s in signals]}

    insights = []
    for s in signals:
        await asyncio.sleep(0.3)
        ins = insight.reason(s, profile)
        insights.append(ins)
        yield {"stage": "reason", "agent": "Insight", "detail": ins.why,
               "signal": s.type, "urgency": ins.urgency, "ev": ins.expected_value}

    for d in orch.decide(insights):
        yield {"stage": "decide", "agent": "Orchestrator",
               "detail": f"{d.action.upper()} — {d.reason}", "signal": d.insight.signal.type}
        if d.action != "fire":
            continue
        await asyncio.sleep(0.3)
        nudge = eng.explain(d)
        yield {"stage": "explain", "agent": "Engagement",
               "detail": nudge.message, "nudge": nudge.model_dump()}
        if auto_approve:
            res = action.act(nudge, profile)
            yield {"stage": "act", "agent": "Action",
                   "detail": res.get("result") or res.get("reason"),
                   "executed": res["executed"], "tool": nudge.tool}

    yield {"stage": "done", "agent": "System", "detail": "Pipeline complete"}
