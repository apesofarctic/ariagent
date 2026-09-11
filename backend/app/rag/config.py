"""Where the retrieval layer's models and artifacts live.

Everything is env-overridable so the same code runs on a laptop with no
credentials (ONNX models on CPU, numpy index on disk) and, unchanged, against a
managed vector store if this ever left the hackathon bench.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = REPO_ROOT / "knowledge"


@dataclass(frozen=True)
class RagConfig:
    passages: Path = field(default_factory=lambda: KNOWLEDGE / "passages.jsonl")
    index_dir: Path = field(default_factory=lambda: KNOWLEDGE / "index")
    dense_model: str = field(
        default_factory=lambda: os.environ.get("ARIAGENT_DENSE_MODEL", "BAAI/bge-base-en-v1.5")
    )
    sparse_model: str = field(
        default_factory=lambda: os.environ.get("ARIAGENT_SPARSE_MODEL", "prithivida/Splade_PP_en_v1")
    )
    reranker_model: str = field(
        default_factory=lambda: os.environ.get("ARIAGENT_RERANKER", "BAAI/bge-reranker-base")
    )
    # bge asks for this prefix on the query side only; passages go in bare.
    dense_query_prefix: str = "Represent this sentence for searching relevant passages: "
    candidates: int = 40          # per retriever, before fusion
    rrf_k: int = 60               # reciprocal rank fusion constant
    rerank_depth: int = 25        # how deep the cross-encoder re-scores
    top_k: int = 5                # what the agent actually sees


def get_config() -> RagConfig:
    return RagConfig()
