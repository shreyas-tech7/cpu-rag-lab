# Changelog

## v0.1.0-rc1 (2026-11-20)

Release commit: `RELEASE_SHA_PLACEHOLDER`

First release candidate.

- Corpora: self-made docs from FastAPI, uv and HTTPX with heading queries, SciFact (full and a seeded pool of 1,000 abstracts), and a built-in toy corpus.
- Chunkers: fixed size with overlap, sentence and heading.
- Retrievers: BM25 from scratch, dense search with FastEmbed (all-MiniLM-L6-v2 ONNX) and hybrid search with reciprocal rank fusion.
- Metrics: Recall@5, Recall@10, MRR@10 and nDCG@10 with 95% bootstrap intervals over queries, latency p50 and p95, peak RSS and index build time.
- A resumable grid runner with a 2 GB memory guard, and `run`, `status` and `report` commands.
- Generated README tables, decision guide and a static site that opens from disk.
- Checked-in results for the default and tiny grids.
- CI on Python 3.11, a manual heavy-grid workflow, issue templates and a social preview.

Known gaps: bge-small-en-v1.5 and the reranker are blocked on the build machine. See `BLOCKERS.md`.
