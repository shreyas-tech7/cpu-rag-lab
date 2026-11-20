"""The resumable grid runner.

Each run moves through four states: pending, running, done and failed. A journal file
(`<results>.state.jsonl`) records each move. `results.jsonl` holds one line per finished
run (done or failed). On start the runner reads both files. Done and failed runs are
skipped. A run that the journal shows as running but that has no result line was cut
off by a stop, so it goes back to pending and runs again.
"""

from __future__ import annotations

import datetime as dt
import itertools
import json
import os
import platform
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import corpus as corpus_mod
from .bm25 import BM25
from .chunkers import chunk_corpus
from .embedders import get_embedder
from .memguard import LIMIT_MB, MemGuard
from .metrics import per_query, percentile, summarize
from .retrieve import DEPTH, dense_search, rrf, to_units

PENDING, RUNNING, DONE, FAILED = "pending", "running", "done", "failed"
RETRIEVERS = ("bm25", "dense", "hybrid")
AXES = ("chunkers", "sizes", "overlaps", "retrievers", "models")  # a corpus entry can override


@dataclass(frozen=True)
class RunSpec:
    corpus: str
    chunker: str
    size: int
    overlap: float
    retriever: str
    model: str  # "-" for bm25

    @property
    def run_id(self) -> str:
        return "|".join(
            [self.corpus, self.chunker, str(self.size), f"{self.overlap:g}"]
            + [self.retriever, self.model]
        )


def expand(cfg: dict) -> list[RunSpec]:
    """Every run in the grid, in the order the runner does them."""
    out = []
    for entry in cfg["corpora"]:
        c = {"name": entry} if isinstance(entry, str) else entry
        ax = {
            k: c.get(k, cfg[k]) for k in ("chunkers", "sizes", "overlaps", "retrievers", "models")
        }
        for ch, s, o in itertools.product(ax["chunkers"], ax["sizes"], ax["overlaps"]):
            for r in ax["retrievers"]:
                models = ["-"] if r == "bm25" else ax["models"]
                out.extend(RunSpec(c["name"], ch, s, o, r, m) for m in models)
    return out


def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def _append(path: Path, row: dict) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a line cut off by a hard stop
    return rows


def states(results: Path) -> dict[str, str]:
    """Current state of each run id seen so far. Missing ids are pending."""
    journal = Path(str(results).replace(".jsonl", ".state.jsonl"))
    st: dict[str, str] = {}
    for e in read_jsonl(journal):
        st[e["run_id"]] = e["status"]
    for r in read_jsonl(results):
        st[r["run_id"]] = r["status"]
    # A run left in `running` was cut off. It goes back to pending.
    return {k: (PENDING if v == RUNNING else v) for k, v in st.items()}


class Runner:
    def __init__(self, cfg: dict, results: Path, retry_failed: bool = False, log=print):
        self.cfg, self.results, self.log = cfg, Path(results), log
        self.journal = Path(str(self.results).replace(".jsonl", ".state.jsonl"))
        self.retry_failed = retry_failed
        self.threads = cfg.get("threads", 2)
        self.limit_mb = cfg.get("memory_limit_mb", LIMIT_MB)

    def _mark(self, run_id: str, status: str) -> None:
        _append(self.journal, {"run_id": run_id, "status": status, "ts": time.time()})

    def todo(self) -> list[RunSpec]:
        st = states(self.results)
        skip = {DONE} | (set() if self.retry_failed else {FAILED})
        return [s for s in expand(self.cfg) if st.get(s.run_id, PENDING) not in skip]

    def run(self, should_stop: Callable[[RunSpec], bool] | None = None) -> int:
        """Run every pending run. Returns how many runs finished in this call."""
        todo = self.todo()
        self.log(f"{len(todo)} runs to do, {len(expand(self.cfg)) - len(todo)} already finished")
        finished = 0
        groups: dict[tuple, list[RunSpec]] = {}
        for s in todo:
            groups.setdefault((s.corpus, s.chunker, s.size, s.overlap), []).append(s)
        loaded: dict[str, corpus_mod.Corpus] = {}
        embedders: dict[str, object] = {}
        with MemGuard(self.limit_mb) as guard:
            for (cname, chunker, size, overlap), specs in groups.items():
                if cname not in loaded:
                    loaded.clear()
                    loaded[cname] = self._load(cname)
                corp = loaded[cname]
                guard.reset()
                state = _GroupState(corp, chunk_corpus(corp.docs, chunker, size, overlap))
                for spec in specs:
                    if should_stop and should_stop(spec):
                        self.log("stop requested")
                        return finished
                    self._mark(spec.run_id, RUNNING)
                    t0 = time.perf_counter()
                    try:
                        row = self._one(spec, state, embedders, guard)
                    except Exception as e:  # noqa: BLE001 - a failed run is a result
                        row = self._base(spec, state)
                        row.update(status=FAILED, error=f"{type(e).__name__}: {e}")
                    row["wall_s"] = round(time.perf_counter() - t0, 3)
                    row["peak_rss_mb"] = round(guard.peak_mb, 1)
                    _append(self.results, row)
                    self._mark(spec.run_id, row["status"])
                    finished += 1
                    self.log(f"{row['status']:6} {spec.run_id} {row['wall_s']}s")
        return finished

    def _load(self, name: str) -> corpus_mod.Corpus:
        corp = corpus_mod.load(name)
        mq = self.cfg.get("max_queries")
        if mq:
            corp.queries = corp.queries[:mq]
        return corp

    def _base(self, spec: RunSpec, state: _GroupState) -> dict:
        return {
            "run_id": spec.run_id,
            "corpus": spec.corpus,
            "chunker": spec.chunker,
            "size": spec.size,
            "overlap": spec.overlap,
            "retriever": spec.retriever,
            "model": spec.model,
            "n_docs": len(state.corp.docs),
            "n_chunks": len(state.chunks),
            "n_queries": len(state.corp.queries),
            "grid": self.cfg["name"],
            "seed": self.cfg.get("seed", 0),
            "threads": self.threads,
            "cpu": cpu_model(),
            "date": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d"),
            "memory_limit_mb": self.limit_mb,
        }

    def _one(self, spec: RunSpec, state: _GroupState, embedders: dict, guard: MemGuard) -> dict:
        row = self._base(spec, state)
        build_s = 0.0
        if spec.retriever in ("bm25", "hybrid"):
            build_s += state.bm25(guard)
        emb = None
        if spec.retriever in ("dense", "hybrid"):
            if spec.model not in embedders:
                embedders[spec.model] = get_embedder(spec.model, threads=self.threads)
            emb = embedders[spec.model]
            build_s += state.vectors(spec.model, emb, guard)
        lat, rows = [], []
        n = self.cfg.get("depth", DEPTH)
        for q in state.corp.queries:
            t = time.perf_counter()
            if spec.retriever == "bm25":
                ranked = state.index.search(q.text, n)
            elif spec.retriever == "dense":
                ranked = dense_search(state.mats[spec.model], emb.embed_query(q.text), n)
            else:
                a = state.index.search(q.text, n)
                b = dense_search(state.mats[spec.model], emb.embed_query(q.text), n)
                ranked = rrf([a, b])
            units = to_units(ranked, state.chunks, 10)
            lat.append((time.perf_counter() - t) * 1000)
            rows.append(per_query(units, q.relevant))
            guard.check()
        row.update(
            status=DONE,
            metrics=summarize(rows),
            latency_ms={"p50": round(percentile(lat, 50), 3), "p95": round(percentile(lat, 95), 3)},
            index_build_s=round(build_s, 3),
        )
        return row


class _GroupState:
    """Chunks, the BM25 index and the embedding matrices for one chunk setting."""

    def __init__(self, corp: corpus_mod.Corpus, chunks):
        self.corp, self.chunks = corp, chunks
        self.index: BM25 | None = None
        self.bm25_s = 0.0
        self.mats: dict[str, np.ndarray] = {}
        self.embed_s: dict[str, float] = {}

    def bm25(self, guard: MemGuard) -> float:
        if self.index is None:
            t = time.perf_counter()
            self.index = BM25([c.text for c in self.chunks])
            self.bm25_s = time.perf_counter() - t
            guard.check()
        return self.bm25_s

    def vectors(self, model: str, emb, guard: MemGuard) -> float:
        if model not in self.mats:
            t = time.perf_counter()
            self.mats[model] = emb.embed([c.text for c in self.chunks], on_batch=guard.check)
            self.embed_s[model] = time.perf_counter() - t
        return self.embed_s[model]


def load_config(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())
