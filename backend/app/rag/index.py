"""Build and load the three indexes the retriever fuses.

  lexical  rank_bm25 Okapi over tokenised passage text
  dense    BAAI/bge-base-en-v1.5, 768d, ONNX on CPU via fastembed
  sparse   SPLADE++ (prithivida/Splade_PP_en_v1) learned term expansion

Dense and sparse vectors are cached on disk keyed by model name and corpus
checksum, so an eval sweep pays the encoding cost once.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import re
from pathlib import Path

import numpy as np

from .config import RagConfig, get_config
from .corpus import Passage, load_passages

TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def corpus_fingerprint(passages: tuple[Passage, ...], model: str) -> str:
    h = hashlib.sha256(model.encode())
    for p in passages:
        h.update(p.passage_id.encode())
        h.update(p.text.encode())
    return h.hexdigest()[:16]


class RagIndex:
    def __init__(self, cfg: RagConfig | None = None) -> None:
        self.cfg = cfg or get_config()
        self.passages = load_passages(self.cfg.passages)
        self.cfg.index_dir.mkdir(parents=True, exist_ok=True)
        self._bm25 = None
        self._dense: np.ndarray | None = None
        self._sparse: list[dict[int, float]] | None = None

    # ---------------------------------------------------------------- lexical
    @property
    def bm25(self):
        if self._bm25 is None:
            from rank_bm25 import BM25Okapi

            self._bm25 = BM25Okapi([tokenize(p.text) for p in self.passages])
        return self._bm25

    # ------------------------------------------------------------------ dense
    def _cache(self, kind: str, model: str) -> Path:
        fp = corpus_fingerprint(self.passages, model)
        return self.cfg.index_dir / f"{kind}_{model.replace('/', '_')}_{fp}"

    @property
    def dense(self) -> np.ndarray:
        if self._dense is None:
            path = self._cache("dense", self.cfg.dense_model).with_suffix(".npy")
            if path.exists():
                self._dense = np.load(path)
            else:
                from fastembed import TextEmbedding

                model = TextEmbedding(model_name=self.cfg.dense_model)
                vecs = np.array(list(model.embed([p.text for p in self.passages])), dtype=np.float32)
                vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
                np.save(path, vecs)
                self._dense = vecs
        return self._dense

    def embed_queries(self, queries: list[str]) -> np.ndarray:
        from fastembed import TextEmbedding

        model = TextEmbedding(model_name=self.cfg.dense_model)
        texts = [self.cfg.dense_query_prefix + q for q in queries]
        vecs = np.array(list(model.embed(texts)), dtype=np.float32)
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
        return vecs

    # ----------------------------------------------------------------- sparse
    @property
    def sparse(self) -> list[dict[int, float]]:
        if self._sparse is None:
            path = self._cache("splade", self.cfg.sparse_model).with_suffix(".pkl")
            if path.exists():
                self._sparse = pickle.loads(path.read_bytes())
            else:
                from fastembed import SparseTextEmbedding

                model = SparseTextEmbedding(model_name=self.cfg.sparse_model)
                out = [
                    {int(i): float(v) for i, v in zip(e.indices, e.values)}
                    for e in model.embed([p.text for p in self.passages])
                ]
                path.write_bytes(pickle.dumps(out))
                self._sparse = out
        return self._sparse

    def encode_sparse_queries(self, queries: list[str]) -> list[dict[int, float]]:
        from fastembed import SparseTextEmbedding

        model = SparseTextEmbedding(model_name=self.cfg.sparse_model)
        return [
            {int(i): float(v) for i, v in zip(e.indices, e.values)}
            for e in model.query_embed(queries)
        ]

    # ------------------------------------------------------------------ stats
    def describe(self) -> dict:
        return {
            "passages": len(self.passages),
            "documents": len({p.doc_id for p in self.passages}),
            "dense_model": self.cfg.dense_model,
            "dense_dim": int(self.dense.shape[1]),
            "sparse_model": self.cfg.sparse_model,
            "mean_sparse_terms": round(
                sum(len(v) for v in self.sparse) / len(self.sparse), 1
            ),
        }


if __name__ == "__main__":
    idx = RagIndex()
    print(json.dumps(idx.describe(), indent=2))
