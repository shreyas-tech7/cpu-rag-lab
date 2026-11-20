"""Dense search, hybrid search with reciprocal rank fusion, and chunk-to-unit mapping."""

from __future__ import annotations

import numpy as np

from .bm25 import top_k
from .chunkers import Chunk

RRF_K = 60
DEPTH = 100  # chunks fetched per retriever before fusion and unit mapping


def dense_search(matrix: np.ndarray, qvec: np.ndarray, k: int) -> list[int]:
    """Cosine similarity on L2-normalized vectors is a dot product."""
    if len(matrix) == 0:
        return []
    return top_k(matrix @ qvec, k, positive_only=False)


def rrf(rankings: list[list[int]], k: int = RRF_K) -> list[int]:
    """Reciprocal rank fusion: score(d) = sum over lists of 1 / (k + rank), rank from 1.

    A chunk that sits near the top of either list wins. Raw scores are never compared,
    so BM25 scores and cosine scores need no common scale. Ties break by lower index.
    """
    score: dict[int, float] = {}
    for ranking in rankings:
        for r, d in enumerate(ranking, start=1):
            score[d] = score.get(d, 0.0) + 1.0 / (k + r)
    return sorted(score, key=lambda d: (-score[d], d))


def to_units(ranked_chunks: list[int], chunks: list[Chunk], n: int) -> list[str]:
    """Map a chunk ranking to a ranking of judged units, keeping first appearance."""
    out: list[str] = []
    seen: set[str] = set()
    for i in ranked_chunks:
        for u in chunks[i].units:
            if u not in seen:
                seen.add(u)
                out.append(u)
                if len(out) == n:
                    return out
    return out
