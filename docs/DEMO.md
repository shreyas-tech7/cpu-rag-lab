# Demo

A real terminal session on the build machine (4-core cloud VM, 2026-11-20). Nothing here needs a sign-in, a key or a download. The tiny grid uses the built-in toy corpus and the hash embedder.

The first command stops after 6 runs, like a grid that gets cut off. The second command picks up the other 30 and skips the 6 that are done. BM25 runs go first, then dense and hybrid. The last two commands check the default grid and confirm that the README, the guide and the site match `results/results.jsonl`.

```text
$ .venv/bin/cpu-rag-lab run --config configs/tiny.json --results results/demo.jsonl --max-runs 6
36 runs to do, 0 already finished
done   tiny|fixed|32|0|bm25|- 0.022s
done   tiny|fixed|32|0.2|bm25|- 0.003s
done   tiny|fixed|64|0|bm25|- 0.002s
done   tiny|fixed|64|0.2|bm25|- 0.002s
done   tiny|sentence|32|0|bm25|- 0.002s
done   tiny|sentence|32|0.2|bm25|- 0.003s
stop requested

$ .venv/bin/cpu-rag-lab status --config configs/tiny.json --results results/demo.jsonl
tiny: 36 runs, 30 pending, 6 done, 0 failed

$ .venv/bin/cpu-rag-lab run --config configs/tiny.json --results results/demo.jsonl
30 runs to do, 6 already finished
done   tiny|sentence|64|0|bm25|- 0.018s
done   tiny|sentence|64|0.2|bm25|- 0.003s
done   tiny|heading|32|0|bm25|- 0.003s
done   tiny|heading|32|0.2|bm25|- 0.002s
done   tiny|heading|64|0|bm25|- 0.003s
done   tiny|heading|64|0.2|bm25|- 0.002s
done   tiny|fixed|32|0|dense|hash 0.005s
done   tiny|fixed|32|0|hybrid|hash 0.003s
done   tiny|fixed|32|0.2|dense|hash 0.002s
done   tiny|fixed|32|0.2|hybrid|hash 0.003s
done   tiny|fixed|64|0|dense|hash 0.002s
done   tiny|fixed|64|0|hybrid|hash 0.002s
done   tiny|fixed|64|0.2|dense|hash 0.002s
done   tiny|fixed|64|0.2|hybrid|hash 0.003s
done   tiny|sentence|32|0|dense|hash 0.002s
done   tiny|sentence|32|0|hybrid|hash 0.003s
done   tiny|sentence|32|0.2|dense|hash 0.002s
done   tiny|sentence|32|0.2|hybrid|hash 0.002s
done   tiny|sentence|64|0|dense|hash 0.002s
done   tiny|sentence|64|0|hybrid|hash 0.002s
done   tiny|sentence|64|0.2|dense|hash 0.002s
done   tiny|sentence|64|0.2|hybrid|hash 0.002s
done   tiny|heading|32|0|dense|hash 0.002s
done   tiny|heading|32|0|hybrid|hash 0.003s
done   tiny|heading|32|0.2|dense|hash 0.002s
done   tiny|heading|32|0.2|hybrid|hash 0.002s
done   tiny|heading|64|0|dense|hash 0.002s
done   tiny|heading|64|0|hybrid|hash 0.003s
done   tiny|heading|64|0.2|dense|hash 0.002s
done   tiny|heading|64|0.2|hybrid|hash 0.002s

$ .venv/bin/cpu-rag-lab status --config configs/tiny.json --results results/demo.jsonl
tiny: 36 runs, 0 pending, 36 done, 0 failed

$ head -c 600 results/demo.jsonl
{"chunker": "fixed", "corpus": "tiny", "cpu": "Intel(R) Xeon(R) Processor @ 2.30GHz", "date": "2026-11-20", "grid": "tiny", "index_build_s": 0.001, "latency_ms": {"p50": 0.013, "p95": 0.07}, "memory_limit_mb": 2048, "metrics": {"mrr@10": {"hi": 0.875, "lo": 0.4375, "mean": 0.625}, "ndcg@10": {"hi": 0.9077, "lo": 0.4866, "mean": 0.6905}, "recall@10": {"hi": 1.0, "lo": 0.625, "mean": 0.875}, "recall@5": {"hi": 1.0, "lo": 0.625, "mean": 0.875}}, "model": "-", "n_chunks": 13, "n_docs": 1, "n_queries": 8, "overlap": 0, "peak_rss_mb": 35.9, "retriever": "bm25", "rss_start_mb": 31.0, "run_id": "tiny|

$ .venv/bin/cpu-rag-lab status --config configs/default.json
default: 90 runs, 0 pending, 90 done, 0 failed

$ .venv/bin/cpu-rag-lab report --check
report up to date
```
