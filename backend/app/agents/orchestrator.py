from ..schemas import Insight, Decision


class Orchestrator:
    def __init__(self, max_fires: int = 3, min_urgency: float = 0.3):
        self.max_fires = max_fires
        self.min_urgency = min_urgency

    def decide(self, insights: list[Insight]) -> list[Decision]:
        ranked = sorted(insights, key=lambda i: i.urgency * (1 + i.expected_value / 10000), reverse=True)
        decisions, fired = [], 0
        for ins in ranked:
            if ins.urgency < self.min_urgency:
                decisions.append(Decision(insight=ins, action="suppress", reason="below urgency threshold"))
            elif fired < self.max_fires:
                decisions.append(Decision(insight=ins, action="fire", reason="high priority"))
                fired += 1
            else:
                decisions.append(Decision(insight=ins, action="hold", reason="frequency cap reached"))
        return decisions
