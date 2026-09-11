"""The grounding corpus: RBI's own customer FAQs, one passage per Q/A pair."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .config import get_config


@dataclass(frozen=True)
class Passage:
    passage_id: str
    doc_id: str
    doc_title: str
    section: int
    question: str
    text: str

    def cite(self) -> str:
        return f"[{self.doc_title} - RBI FAQ {self.passage_id}]"


@lru_cache(maxsize=1)
def load_passages(path: Path | None = None) -> tuple[Passage, ...]:
    path = path or get_config().passages
    out: list[Passage] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            out.append(Passage(r["passage_id"], r["doc_id"], r["doc_title"],
                               r["section"], r["question"], r["text"]))
    return tuple(out)
