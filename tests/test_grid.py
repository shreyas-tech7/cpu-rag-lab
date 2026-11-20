import json

from cpu_rag_lab.grid import DONE, FAILED, Runner, expand, read_jsonl, states

CFG = {
    "name": "t",
    "corpora": ["tiny"],
    "chunkers": ["fixed", "heading"],
    "sizes": [32],
    "overlaps": [0, 0.2],
    "retrievers": ["bm25", "dense", "hybrid"],
    "models": ["hash"],
    "seed": 0,
    "threads": 1,
}


def test_expand_counts_and_corpus_overrides():
    assert len(expand(CFG)) == 2 * 2 * 3
    cfg = dict(CFG, corpora=[{"name": "tiny", "chunkers": ["fixed"], "retrievers": ["bm25"]}])
    assert [s.run_id for s in expand(cfg)] == ["tiny|fixed|32|0|bm25|-", "tiny|fixed|32|0.2|bm25|-"]


def test_resume_after_stop_mid_chunk(tmp_path):
    """Broken case: a stop in the middle of a chunk setting loses runs or repeats done ones."""
    out = tmp_path / "r.jsonl"
    calls = {"n": 0}

    def stop_on_fifth(spec):
        calls["n"] += 1
        return calls["n"] == 5  # 4 runs done: one full setting plus one run of the next

    Runner(CFG, out, log=lambda *_: None).run(should_stop=stop_on_fifth)
    assert len(read_jsonl(out)) == 4
    # A hard kill leaves a run marked running in the journal with no result line.
    journal = tmp_path / "r.state.jsonl"
    with journal.open("a") as f:
        f.write(json.dumps({"run_id": "tiny|heading|32|0|bm25|-", "status": "running"}) + "\n")
    assert states(out)["tiny|heading|32|0|bm25|-"] == "pending"
    n = Runner(CFG, out, log=lambda *_: None).run()
    assert n == 8
    rows = read_jsonl(out)
    ids = [r["run_id"] for r in rows]
    assert len(ids) == len(set(ids)) == 12
    assert all(r["status"] == DONE for r in rows)
    assert Runner(CFG, out, log=lambda *_: None).run() == 0


def test_run_rows_have_metrics_intervals_latency_and_memory(tmp_path):
    out = tmp_path / "r.jsonl"
    Runner(dict(CFG, chunkers=["heading"], overlaps=[0]), out, log=lambda *_: None).run()
    for r in read_jsonl(out):
        m = r["metrics"]["recall@10"]
        assert 0 <= m["lo"] <= m["mean"] <= m["hi"] <= 1
        assert r["latency_ms"]["p50"] <= r["latency_ms"]["p95"]
        assert r["peak_rss_mb"] > 0 and r["index_build_s"] >= 0
    bm25 = [r for r in read_jsonl(out) if r["retriever"] == "bm25"][0]
    # 6 of 8 toy headings share a word with their body. "Backing up a laptop" and
    # "Training for a first marathon" do not, so BM25 misses them: the lexical gap.
    assert bm25["metrics"]["recall@10"]["mean"] == 0.75


def test_memory_limit_fails_run_and_grid_continues(tmp_path):
    out = tmp_path / "r.jsonl"
    cfg = dict(CFG, chunkers=["heading"], overlaps=[0], memory_limit_mb=1)
    Runner(cfg, out, log=lambda *_: None).run()
    rows = read_jsonl(out)
    assert len(rows) == 3 and all(r["status"] == FAILED for r in rows)
    assert "MemoryLimitExceeded" in rows[0]["error"]
    # failed runs are skipped on resume unless asked
    assert Runner(cfg, out, log=lambda *_: None).run() == 0
