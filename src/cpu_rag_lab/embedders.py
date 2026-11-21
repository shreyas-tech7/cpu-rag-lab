"""Embedders. The hash embedder is a fake used in tests. Real models run through FastEmbed."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path

import numpy as np

from .bm25 import tokenize
from .corpus import ROOT

BATCH_SIZE = 32


def cache_dir() -> Path:
    return Path(os.environ.get("CPU_RAG_LAB_CACHE", ROOT / ".cache"))


def model_registry() -> dict:
    return json.loads((ROOT / "models.json").read_text())["models"]


class HashEmbedder:
    """Feature hashing of word unigrams and bigrams into `dim` buckets, L2-normalized.

    Deterministic and offline. Texts that share words get similar vectors. It is a
    stand-in for a model in tests, not a semantic embedder.
    """

    name = "hash"

    def __init__(self, dim: int = 384):
        self.dim = dim

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        toks = tokenize(text)
        for f in toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:], strict=False)]:
            h = int.from_bytes(hashlib.blake2b(f.encode(), digest_size=8).digest(), "little")
            v[h % self.dim] += 1.0 if (h >> 63) & 1 else -1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed(self, texts: list[str], on_batch: Callable[[], None] | None = None) -> np.ndarray:
        out = []
        for i in range(0, len(texts), BATCH_SIZE):
            out.extend(self._vec(t) for t in texts[i : i + BATCH_SIZE])
            if on_batch:
                on_batch()
        return np.array(out, dtype=np.float32).reshape(len(texts), self.dim)

    def embed_query(self, text: str) -> np.ndarray:
        return self._vec(text)


class FastEmbedder:
    """A FastEmbed TextEmbedding loaded from a local ONNX folder (see scripts/fetch_models.py)."""

    def __init__(self, name: str, threads: int | None = None):
        from fastembed import TextEmbedding

        spec = model_registry()[name]
        path = cache_dir() / "models" / name / spec.get("subdir", "")
        if not (path / "model.onnx").exists():
            raise FileNotFoundError(
                f"{path}/model.onnx missing. Run: python scripts/fetch_data.py models"
            )
        self.name = name
        self.model = TextEmbedding(
            spec["fastembed_name"],
            specific_model_path=str(path),
            threads=threads,
            enable_cpu_mem_arena=False,  # the arena grew past 2 GB on mixed batch shapes
        )

    def embed(self, texts: list[str], on_batch: Callable[[], None] | None = None) -> np.ndarray:
        out = []
        for i in range(0, len(texts), BATCH_SIZE):
            out.extend(self.model.embed(texts[i : i + BATCH_SIZE], batch_size=BATCH_SIZE))
            if on_batch:
                on_batch()
        dim = len(out[0]) if out else 0
        return np.array(out, dtype=np.float32).reshape(len(texts), dim)

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(next(iter(self.model.query_embed(text))), dtype=np.float32)


def get_embedder(name: str, threads: int | None = None):
    spec = model_registry()[name]
    if spec["kind"] == "hash":
        return HashEmbedder(spec["dim"])
    return FastEmbedder(name, threads=threads)
