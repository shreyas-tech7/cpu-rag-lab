import math

import pytest

from cpu_rag_lab.metrics import (
    bootstrap_ci,
    ndcg_at,
    per_query,
    recall_at,
    reciprocal_rank,
    summarize,
)


def test_recall_mrr_ndcg_known_values():
    ranked, rel = ["a", "b", "c", "d"], {"b", "z"}
    assert recall_at(ranked, rel, 1) == 0
    assert recall_at(ranked, rel, 5) == 0.5
    assert reciprocal_rank(ranked, rel) == 0.5
    want = (1 / math.log2(3)) / (1 + 1 / math.log2(3))
    assert math.isclose(ndcg_at(ranked, rel), want)


def test_mrr_respects_cutoff():
    """Broken case: a hit at rank 11 counted inside MRR@10."""
    assert reciprocal_rank([f"x{i}" for i in range(10)] + ["hit"], {"hit"}) == 0


def test_perfect_ranking_scores_one():
    q = per_query(["a"], {"a"})
    assert q == {"recall@5": 1.0, "recall@10": 1.0, "mrr@10": 1.0, "ndcg@10": 1.0}


def test_bootstrap_is_seeded_and_brackets_the_mean():
    vals = [0, 1] * 50
    a = bootstrap_ci(vals)
    assert a == bootstrap_ci(vals)
    mean, lo, hi = a
    assert mean == 0.5 and lo < 0.5 < hi
    assert 0.08 < hi - lo < 0.3  # about 2 * 1.96 * 0.05


def test_constant_values_have_zero_width_interval():
    assert bootstrap_ci([0.3] * 20) == pytest.approx((0.3, 0.3, 0.3))


def test_summarize_shapes():
    s = summarize([per_query(["a"], {"a"}), per_query(["b"], {"a"})])
    assert s["recall@10"]["mean"] == 0.5
