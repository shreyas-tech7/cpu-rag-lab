# Project context: cpu-rag-lab

## What it is
A lab that measures which retrieval settings work best on a small CPU-only machine.
It runs one grid over chunker, chunk size, overlap, retriever and embedding model.
It reports Recall@5, Recall@10, MRR@10 and nDCG@10 with 95% bootstrap intervals over
queries, plus latency p50 and p95, peak RAM and index build time. A script writes the
README tables, the decision guide and a static site from `results/results.jsonl`.

## Status
v0.1.0-rc1 candidate. See PROGRESS.md and BLOCKERS.md.

## Stack
Python 3.11+, numpy, FastEmbed (ONNX on CPU, no PyTorch), pytest, ruff. Charts are inline SVG.

## Commands
- `./init.sh` makes `.venv`, installs, lints, checks links and runs every test offline.
- `python scripts/fetch_data.py` downloads SciFact, the MiniLM model and the self-made docs, and checks hashes.
- `cpu-rag-lab run --config configs/tiny.json` runs the tiny grid (hash embedder, no download).
- `cpu-rag-lab run --config configs/default.json` runs the default grid. It resumes.
- `cpu-rag-lab status --config configs/default.json` counts pending, done and failed runs.
- `cpu-rag-lab report` writes README tables, `docs/DECISION_GUIDE.md` and `docs/index.html`.
- `cpu-rag-lab report --check` fails if any generated file is stale.

## Layout
- `src/cpu_rag_lab/`: corpus, chunkers, bm25, embedders, retrieve, metrics, memguard, grid, report, svg, cli.
- `configs/`: grid configs. `models.json`: pinned models.
- `data/selfmade/`: committed docs, licenses and manifest. `data/scifact/`: downloaded, not committed.
- `results/`: `results.jsonl` (default grid), `tiny.jsonl`.
- `docs/`: site, guide, study kit, build prompt, hand-off.
- `scripts/`: fetch data, link check, social preview, secret scan.

## Rules
- Tests run offline. `tests/conftest.py` blocks non-local sockets.
- Every number in README and guide comes from `results.jsonl` through `cpu-rag-lab report`.
- No model bigger than a small embedding model. Runs stop over 2 GB RSS.
- Plain English in docs. No em dashes and no semicolons in prose.

## Skills that fit
superpowers test-driven-development, systematic-debugging, verification-before-completion.

## Do not read
`.venv/`, `.cache/`, `data/scifact/`, `data/selfmade/raw/` (large inputs), `logs/`.
