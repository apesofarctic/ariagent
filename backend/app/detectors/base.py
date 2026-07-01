from abc import ABC, abstractmethod
from ..schemas import Transaction, Signal


class Detector(ABC):
    mode: str

    @abstractmethod
    def detect(self, txns: list[Transaction], profile: dict) -> list[Signal]:
        ...
