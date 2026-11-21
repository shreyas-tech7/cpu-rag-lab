"""Ranking metrics per query and percentile bootstrap intervals over queries."""

from __future__ import annotations

import math

import numpy as np

BOOTSTRAP_SAMPLES = 1000
BOOTSTRAP_SEED = 0


def recall_at(ranked: list[str], relevant: set[str], k: int) -> float:
    """Share of the relevant units found in the top k."""
    if not relevant:
        return 0.0
    return len(set(ranked[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked: list[str], relevant: set[str], k: int = 10) -> float:
    """1 / rank of the first relevant unit in the top k, else 0. MRR is its mean."""
    for i, u in enumerate(ranked[:k], start=1):
        if u in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at(ranked: list[str], relevant: set[str], k: int = 10) -> float:
    """Binary-gain nDCG: DCG of the ranking divided by DCG of an ideal ranking."""
    dcg = sum(1.0 / math.log2(i + 1) for i, u in enumerate(ranked[:k], 1) if u in relevant)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal else 0.0


def per_query(ranked: list[str], relevant: set[str]) -> dict[str, float]:
    return {
        "recall@5": recall_at(ranked, relevant, 5),
        "recall@10": recall_at(ranked, relevant, 10),
        "mrr@10": reciprocal_rank(ranked, relevant, 10),
        "ndcg@10": ndcg_at(ranked, relevant, 10),
    }


def bootstrap_ci(
    values: list[float],
    n: int = BOOTSTRAP_SAMPLES,
    seed: int = BOOTSTRAP_SEED,
    level: float = 0.95,
) -> tuple[float, float, float]:
    """Mean and a percentile bootstrap interval, resampling queries with replacement.

    The interval shows how much the mean would move with a different set of queries
    drawn from the same pool. It says nothing about other corpora.
    """
    x = np.asarray(values, dtype=np.float64)
    if len(x) == 0:
        return (0.0, 0.0, 0.0)
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), size=(n, len(x)))].mean(axis=1)
    lo, hi = np.quantile(means, [(1 - level) / 2, 1 - (1 - level) / 2])
    return (float(x.mean()), float(lo), float(hi))


def percentile(values: list[float], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), q)) if values else 0.0


def summarize(rows: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    """Mean and 95% interval for each metric over the per-query rows."""
    out = {}
    for m in ("recall@5", "recall@10", "mrr@10", "ndcg@10"):
        mean, lo, hi = bootstrap_ci([r[m] for r in rows])
        out[m] = {"mean": round(mean, 4), "lo": round(lo, 4), "hi": round(hi, 4)}
    return out
