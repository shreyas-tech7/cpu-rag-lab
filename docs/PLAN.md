# Plan: cpu-rag-lab

Goal: measure which chunker, chunk size, overlap and retriever work best on a small CPU, with honest intervals, and write a decision guide in which every number comes from a run.

Architecture: a Python package (`src/cpu_rag_lab`) with one module per pipeline step, a resumable grid runner that appends to `results/results.jsonl`, and a report writer that fills the README, the guide and a static site from that file.

Tech: Python 3.11+, numpy, FastEmbed (ONNX, CPU), pytest, ruff. No vector database, no GPU, no LLM.

## Assumptions (also in DECISIONS.md)
- The brief is the spec. No question rounds.
- Hugging Face may be blocked. Fall back to any model with a checkable hash, else BM25 plus the hash embedder.
- The self-made heading queries are a proxy and are labelled as one.
- Default grid time target about 20 minutes on the 4-core VM. Cut the SciFact pool before cutting grid axes.

## Tasks, in build order
1. Initializer: `init.sh`, memory files, network guard, license, gitleaks hook. Verify: `./init.sh`.
2. Corpus loaders and the hash embedder. Verify: `pytest tests/test_corpus.py tests/test_retrieve.py -k hash`.
3. Chunkers (fixed, sentence, heading), sized in words, each chunk tagged with its sections. Verify: `pytest tests/test_chunkers.py`.
4. BM25 from scratch, checked against the formula by hand. Verify: `pytest tests/test_bm25.py`.
5. Metrics and bootstrap intervals. Verify: `pytest tests/test_metrics.py`.
6. Grid runner: pending, running, done, failed; journal file; memory watchdog; timing. Verify: `pytest tests/test_grid.py tests/test_memguard.py` (includes a stop in the middle of a chunk setting).
7. Dense search with FastEmbed, hybrid with RRF. Verify: `pytest tests/test_retrieve.py` and a 3-text embed.
8. Reranker if an ONNX cross-encoder is reachable. Else log it as blocked.
9. Tiny grid on 2 cores, then the default grid in the background.
10. Report: README blocks, decision guide, static site, number-match tests. Verify: `pytest tests/test_report.py` and `cpu-rag-lab report --check`.
11. README, study kit, release check, hand-off.
