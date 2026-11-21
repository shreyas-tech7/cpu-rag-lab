import numpy as np

from cpu_rag_lab.chunkers import Chunk
from cpu_rag_lab.embedders import HashEmbedder
from cpu_rag_lab.retrieve import dense_search, rrf, to_units


def test_rrf_rewards_agreement():
    """Broken case: fusion that just appends the second list after the first."""
    a, b = [1, 2, 3], [3, 4, 1]
    fused = rrf([a, b])
    assert fused[0] in (1, 3)
    assert set(fused[:2]) == {1, 3}
    assert fused[-1] == 4 or fused[-1] == 2


def test_rrf_formula():
    fused = rrf([[7], [8, 7]], k=60)
    # 7: 1/61 + 1/62, 8: 1/61
    assert fused == [7, 8]


def test_to_units_dedupes_and_keeps_order():
    chunks = [Chunk("c0", "", ("u1",)), Chunk("c1", "", ("u1", "u2")), Chunk("c2", "", ("u3",))]
    assert to_units([1, 0, 2], chunks, 10) == ["u1", "u2", "u3"]
    assert to_units([2, 1], chunks, 2) == ["u3", "u1"]


def test_hash_embedder_is_deterministic_and_normalized():
    e = HashEmbedder(64)
    m = e.embed(["green tea leaves", "green tea", "car engine oil"])
    assert np.allclose(np.linalg.norm(m, axis=1), 1, atol=1e-5)
    assert np.array_equal(m, e.embed(["green tea leaves", "green tea", "car engine oil"]))
    q = e.embed_query("green tea")
    assert dense_search(m, q, 3)[0] == 1
    assert dense_search(m, q, 3)[-1] == 2
