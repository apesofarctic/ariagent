from datetime import date
from typing import Literal
from pydantic import BaseModel

Mode = Literal["protect", "grow", "guide"]


class Transaction(BaseModel):
    date: date
    amount: float          # negative = debit, positive = credit
    merchant: str
    category: str


class Signal(BaseModel):
    type: str
    mode: Mode
    confidence: float
    evidence: list[str]
    data: dict = {}


class Insight(BaseModel):
    signal: Signal
    urgency: float
    expected_value: float
    why: str


class Decision(BaseModel):
    insight: Insight
    action: Literal["fire", "hold", "suppress", "sequence"]
    reason: str


class Nudge(BaseModel):
    title: str
    message: str
    action_label: str
    tool: str
    tool_args: dict
    mode: Mode = "protect"
    reasoning: list[str] = []          # visible reasoning trace ("why")
    regulated: bool = False            # SIP / insurance / money-move → disclaimer
    reversible: bool = True
    journey: list[str] | None = None   # multi-step Guide journeys
