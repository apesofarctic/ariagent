"""Phase 1.3 — embedding classifier challenger.

Encodes raw merchant strings with bge-small-en-v1.5 (384d, ONNX, CPU via
fastembed), fits a linear classifier on top, and falls back to kNN over
the embedding space for classes too thin for the linear head to learn
cleanly (the long tail).
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier

_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_LONG_TAIL_MIN_COUNT = 30   # classes with fewer train examples than this go to kNN
_KNN_REFERENCE_CAP = 20_000  # bound brute-force kNN cost; only the long tail needs it


class EmbeddingCategorizer:
    def __init__(self, knn_neighbors: int = 5, threads: int = 8, batch_size: int = 256):
        self.knn_neighbors = knn_neighbors
        self.threads = threads
        self.batch_size = batch_size
        self._embedder = None
        self.linear = LogisticRegression(max_iter=1000, C=2.0)
        self.knn = KNeighborsClassifier(n_neighbors=knn_neighbors)
        self.long_tail_classes: set[str] = set()

    @property
    def embedder(self):
        if self._embedder is None:
            from fastembed import TextEmbedding
            self._embedder = TextEmbedding(model_name=_MODEL_NAME, threads=self.threads)
        return self._embedder

    def _encode(self, texts) -> np.ndarray:
        return np.array(list(self.embedder.embed(list(texts), batch_size=self.batch_size)))

    def fit(self, raw_merchants, categories) -> "EmbeddingCategorizer":
        X = self._encode(raw_merchants)
        y = np.asarray(categories)
        counts = {c: int((y == c).sum()) for c in set(y)}
        self.long_tail_classes = {c for c, n in counts.items() if n < _LONG_TAIL_MIN_COUNT}

        self.linear.fit(X, y)

        # kNN only ever has to resolve the long-tail / low-confidence residual,
        # so a bounded random reference set keeps brute-force distance cost sane
        if len(X) > _KNN_REFERENCE_CAP:
            rng = np.random.default_rng(0)
            ref_idx = rng.choice(len(X), size=_KNN_REFERENCE_CAP, replace=False)
        else:
            ref_idx = np.arange(len(X))
        self.knn.fit(X[ref_idx], y[ref_idx])
        return self

    def predict(self, raw_merchants) -> np.ndarray:
        X = self._encode(raw_merchants)
        linear_preds = self.linear.predict(X)
        proba = self.linear.predict_proba(X)
        max_proba = proba.max(axis=1)
        low_confidence = max_proba < 0.35
        use_knn = low_confidence | np.isin(linear_preds, list(self.long_tail_classes))

        out = linear_preds.copy()
        if use_knn.any():
            out[use_knn] = self.knn.predict(X[use_knn])
        return out
