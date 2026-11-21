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

    def stop_on_sixth(spec):
        calls["n"] += 1
        # BM25 runs go first (4), then dense and hybrid by chunk setting. Stopping before
        # the sixth run leaves the fixed|0 setting half done: dense finished, hybrid not.
        return calls["n"] == 6

    Runner(CFG, out, log=lambda *_: None).run(should_stop=stop_on_sixth)
    assert len(read_jsonl(out)) == 5
    # A hard kill leaves a run marked running in the journal with no result line.
    journal = tmp_path / "r.state.jsonl"
    with journal.open("a") as f:
        f.write(json.dumps({"run_id": "tiny|fixed|32|0|hybrid|hash", "status": "running"}) + "\n")
    assert states(out)["tiny|fixed|32|0|hybrid|hash"] == "pending"
    n = Runner(CFG, out, log=lambda *_: None).run()
    assert n == 7
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


def test_journal_name_works_for_any_suffix(tmp_path):
    """Broken case: --results out.json made the journal the same file as the results."""
    from cpu_rag_lab.grid import journal_path

    assert journal_path(tmp_path / "out.json") == tmp_path / "out.json.state.jsonl"
    assert journal_path(tmp_path / "r.jsonl") == tmp_path / "r.state.jsonl"
    out = tmp_path / "out.json"
    Runner(dict(CFG, chunkers=["fixed"], overlaps=[0]), out, log=lambda *_: None).run()
    assert all("metrics" in r for r in read_jsonl(out))


def test_half_written_line_does_not_lose_the_next_row(tmp_path):
    """Broken case: a cut-off last line glued onto the next row, so both were dropped."""
    out = tmp_path / "r.jsonl"
    cfg = dict(CFG, chunkers=["fixed"], overlaps=[0])
    Runner(cfg, out, log=lambda *_: None).run(should_stop=lambda s: s.retriever == "hybrid")
    with out.open("a") as f:
        f.write('{"run_id": "tiny|fixed|32|0|hybr')  # hard stop mid-write
    Runner(cfg, out, log=lambda *_: None).run()
    ids = [r["run_id"] for r in read_jsonl(out)]
    assert sorted(ids) == sorted(s.run_id for s in expand(cfg))


def test_journal_done_without_result_row_runs_again(tmp_path):
    out = tmp_path / "r.jsonl"
    rid = "tiny|fixed|32|0|bm25|-"
    (tmp_path / "r.state.jsonl").write_text(json.dumps({"run_id": rid, "status": "done"}) + "\n")
    assert states(out).get(rid, "pending") == "pending"


def test_peak_is_measured_per_run(tmp_path, monkeypatch):
    """Broken case: the peak was reset once per chunk setting, so later runs inherited it."""
    from cpu_rag_lab import memguard

    out = tmp_path / "r.jsonl"
    cfg = dict(CFG, chunkers=["fixed"], overlaps=[0], retrievers=["bm25", "dense"])
    # 900 MB while the first run is going, 100 MB after its row is written.
    fake = lambda *_: 100.0 if out.exists() and out.read_text() else 900.0  # noqa: E731
    monkeypatch.setattr(memguard, "rss_mb", fake)
    Runner(cfg, out, log=lambda *_: None).run()
    assert [r["peak_rss_mb"] for r in read_jsonl(out)] == [900.0, 100.0]


def test_retry_failed_report_counts_each_run_once(tmp_path):
    from cpu_rag_lab.report import latest_rows

    out = tmp_path / "r.jsonl"
    cfg = dict(CFG, chunkers=["heading"], overlaps=[0], memory_limit_mb=1)
    Runner(cfg, out, log=lambda *_: None).run()
    Runner(dict(cfg, memory_limit_mb=2048), out, retry_failed=True, log=lambda *_: None).run()
    rows = latest_rows(read_jsonl(out))
    assert len(rows) == 3 and all(r["status"] == DONE for r in rows)
