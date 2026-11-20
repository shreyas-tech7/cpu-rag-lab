import math

import numpy as np

from cpu_rag_lab.bm25 import BM25, tokenize, top_k


def test_tokenize_lowercases_and_drops_stopwords():
    assert tokenize("The Cat, and THE hat!") == ["cat", "hat"]


def test_score_matches_hand_formula():
    """Broken case: idf or length normalization computed wrong."""
    texts = ["cat cat dog", "dog bird", "fish"]
    bm = BM25(texts, k1=1.2, b=0.75)
    avgdl = (3 + 2 + 1) / 3
    idf = math.log(1 + (3 - 1 + 0.5) / (1 + 0.5))
    tf, dl = 2, 3
    want = idf * tf * 2.2 / (tf + 1.2 * (1 - 0.75 + 0.75 * dl / avgdl))
    assert math.isclose(bm.scores("cat")[0], want, rel_tol=1e-9)
    assert bm.scores("cat")[1] == 0


def test_search_ranks_best_first_and_drops_non_matches():
    bm = BM25(["green tea leaves", "black coffee", "tea tea tea"])
    assert bm.search("tea", 3) == [2, 0]


def test_top_k_keeps_negative_scores_when_asked():
    assert top_k(np.array([-0.5, -0.1, -0.9]), 2, positive_only=False) == [1, 0]


def test_top_k_ties_at_the_cutoff_go_to_the_lower_index():
    """Broken case: argpartition picked any of the tied scores at the cutoff."""
    assert top_k(np.array([1.0] * 10 + [2.0]), 3) == [10, 0, 1]
    assert top_k(np.ones(300), 3) == [0, 1, 2]
