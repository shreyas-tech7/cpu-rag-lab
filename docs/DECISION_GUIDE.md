# Decision guide

This guide is written by `cpu-rag-lab report` from `results/results.jsonl`. Do not edit it by hand.

Source: 90 finished runs on 2026-11-20, Intel(R) Xeon(R) Processor @ 2.30GHz, 4 threads. Model: minilm. Intervals are 95% percentile bootstrap intervals over queries, 1000 resamples, seed 0. Main score: nDCG@10.

## self-made docs (fastapi, uv, httpx)

- **Best setting:** hybrid (minilm), heading 512 words, 0% overlap. nDCG@10 0.614 [0.582, 0.645], Recall@10 0.845 [0.814, 0.873], p95 latency 2.93 ms, 574 queries.
- **Close calls:** 5 other settings have a mean nDCG@10 inside the best setting's interval. Treat them as ties with this many queries.
- **Fast pick inside that interval:** hybrid (minilm), heading 128 words, 20% overlap. nDCG@10 0.613, p95 latency 2.62 ms, build 32.89 s.

### Retriever

| Retriever | Best nDCG@10 [95% CI] | Its setting | Mean nDCG@10 over all its runs | Median p50 ms |
|---|---|---|---|---|
| bm25 | 0.570 [0.539, 0.601] | bm25, heading 256 words, 0% overlap | 0.441 | 0.03 |
| dense | 0.541 [0.508, 0.574] | dense (minilm), heading 128 words, 0% overlap | 0.402 | 1.86 |
| hybrid | 0.614 [0.582, 0.645] | hybrid (minilm), heading 512 words, 0% overlap | 0.466 | 2.04 |

Best dense against best BM25: bm25 is ahead, and the intervals overlap, so the gap may be noise.
Best hybrid search with reciprocal rank fusion is ahead of the best single retriever (0.614 against 0.570), and the intervals overlap, so the gap may be noise.

### Chunk size

Mean over the other settings at each size. Build time is the mean index build time.

| Retriever | 128 words | 256 words | 512 words |
|---|---|---|---|
| bm25 | nDCG 0.479, p50 0.04 ms, build 0.05 s | nDCG 0.441, p50 0.03 ms, build 0.04 s | nDCG 0.402, p50 0.03 ms, build 0.04 s |
| dense | nDCG 0.455, p50 1.97 ms, build 35.07 s | nDCG 0.398, p50 1.94 ms, build 32.14 s | nDCG 0.353, p50 1.87 ms, build 25.13 s |
| hybrid | nDCG 0.512, p50 2.09 ms, build 35.12 s | nDCG 0.463, p50 2.15 ms, build 32.18 s | nDCG 0.423, p50 2.01 ms, build 25.19 s |

Across all retrievers, 128-word chunks score best on average (mean nDCG@10 0.482).

### Overlap and chunker

- **Overlap**, mean nDCG@10: 0%: 0.435, 20%: 0.438.
- **Chunker**, mean nDCG@10: fixed: 0.360, heading: 0.571, sentence: 0.378.

## SciFact, 1,000-abstract pool

- **Best setting:** hybrid (minilm), sentence 512 words, 0% overlap. nDCG@10 0.822 [0.783, 0.857], Recall@10 0.908 [0.874, 0.940], p95 latency 4.98 ms, 300 queries.
- **Close calls:** 23 other settings have a mean nDCG@10 inside the best setting's interval. Treat them as ties with this many queries.
- **Fast pick inside that interval:** bm25, sentence 256 words, 20% overlap. nDCG@10 0.784, p95 latency 0.13 ms, build 0.18 s.

### Retriever

| Retriever | Best nDCG@10 [95% CI] | Its setting | Mean nDCG@10 over all its runs | Median p50 ms |
|---|---|---|---|---|
| bm25 | 0.784 [0.742, 0.823] | bm25, sentence 256 words, 20% overlap | 0.776 | 0.07 |
| dense | 0.814 [0.778, 0.850] | dense (minilm), sentence 128 words, 20% overlap | 0.799 | 8.09 |
| hybrid | 0.822 [0.783, 0.857] | hybrid (minilm), sentence 512 words, 0% overlap | 0.817 | 11.87 |

Best dense against best BM25: dense is ahead, and the intervals overlap, so the gap may be noise.
Best hybrid search with reciprocal rank fusion is ahead of the best single retriever (0.822 against 0.814), and the intervals overlap, so the gap may be noise.

### Chunk size

Mean over the other settings at each size. Build time is the mean index build time.

| Retriever | 128 words | 256 words | 512 words |
|---|---|---|---|
| bm25 | nDCG 0.764, p50 0.10 ms, build 0.18 s | nDCG 0.782, p50 0.07 ms, build 0.18 s | nDCG 0.783, p50 0.07 ms, build 0.17 s |
| dense | nDCG 0.802, p50 12.87 ms, build 58.79 s | nDCG 0.797, p50 11.06 ms, build 79.91 s | nDCG 0.800, p50 3.02 ms, build 58.89 s |
| hybrid | nDCG 0.812, p50 11.94 ms, build 59.06 s | nDCG 0.816, p50 13.63 ms, build 80.13 s | nDCG 0.821, p50 3.52 ms, build 59.08 s |

Across all retrievers, 512-word chunks score best on average (mean nDCG@10 0.801).

### Overlap and chunker

- **Overlap**, mean nDCG@10: 0%: 0.795, 20%: 0.800.
- **Chunker**, mean nDCG@10: fixed: 0.797, sentence: 0.798.

## Memory and time

- Highest peak RSS in a finished run: 1,416 MB. The guard stops any run over 2,048 MB.
- Total run time of the grid: 24.5 minutes for 90 runs.
- Failed runs: 0.

## Limits

- Self-made queries are section headings. They are a proxy for real questions and favor words that the docs already use.
- The SciFact pool is cut down for time. A smaller pool makes retrieval easier than the full benchmark.
- MiniLM reads at most 256 tokens, so long chunks are cut short for dense search.
- A retrieved chunk gives credit to every section its words come from. A long fixed or sentence chunk can span several short sections, while a heading chunk spans one. This favors long chunks a little and heading chunks on the self-made corpus.
- One machine, one model and one seed for the bootstrap. Timings move with the machine.
