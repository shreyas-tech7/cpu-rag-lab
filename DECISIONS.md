# Decisions

One line per choice: the options weighed and the reason.

- Name: `cpu-rag-lab`. Checked 2026-11-20: `pypi.org/pypi/cpu-rag-lab/json` 404, `registry.npmjs.org/cpu-rag-lab` 404, no well-known GitHub project with that name. It matches the repo, so no rename.
- Base branch: GitHub origin was empty when cloned, so the branch `claude/build-cpu-rag-lab` starts from the `main` in the build session's clone (one README commit by Shreyas). Options: start from an empty root, or from that commit. That commit keeps one shared history.
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (Apache-2.0) from Chroma's public S3 export, loaded by FastEmbed from a local folder. Options: the brief's default `BAAI/bge-small-en-v1.5`, npm republishes of model files, or BM25 plus the hash embedder only. Hugging Face answered 403 and the old FastEmbed GCS mirror answered AccessDenied, so bge-small could not be fetched. The Chroma archive has its SHA-256 pinned in Chroma's own source code, which gives a checkable origin. Obscure npm republishes have no checkable origin, so they were not used.
- Only one real embedding model, not two or three. Every other FastEmbed model downloads only from Hugging Face. Logged in BLOCKERS.md.
- Reranker: off. Every FastEmbed cross-encoder lives on Hugging Face. The MVP lists it as optional.
- Public dataset: SciFact from `scifact.s3-us-west-2.amazonaws.com` (archive SHA-256 recorded). License CC BY-NC 2.0, which allows non-commercial reuse with credit. This repo is a free, non-commercial lab, and it does not commit the data. It downloads and checks the hash. Options: BEIR mirrors (blocked), Cranfield copies on GitHub (license unclear), or self-made only.
- SciFact queries: the 300 dev claims, relevant docs from `cited_doc_ids`, matching the BEIR SciFact test split.
- SciFact pool for the default grid: 1,000 abstracts (all 339 cited ones plus 661 drawn with seed 0), named `scifact1000`. The full 5,183 pool needs about 143,000 chunk embeddings over the grid, about 80 minutes on this VM. A smaller pool is an easier task, and the README says so.
- SciFact chunkers: fixed and sentence only. Each SciFact abstract is one section, so the heading chunker makes the same chunks as the sentence chunker. Running it would repeat runs.
- Self-made corpus: 91 Markdown docs from fastapi/fastapi (MIT), astral-sh/uv (MIT or Apache-2.0) and encode/httpx (BSD-3-Clause), at pinned commits, with license files and per-file SHA-256 in `data/selfmade/manifest.json`. These files are committed so the lab runs offline. The licenses allow it.
- Self-made queries: one per section heading, skipping generic headings, repeated headings, one-word headings and sections under 30 words. The heading line is removed from the section text so a query does not match its own line.
- Code blocks and include tags are dropped from the self-made docs. The lab measures retrieval over prose.
- Chunk size counts whitespace words, as the brief says. MiniLM reads at most 256 tokens, so a 512-word chunk is cut short for dense search. The README says so.
- k: the brief's k of 5 and 10 are metrics on one ranking (Recall@5 and Recall@10), not separate runs. Retrieval depth is 100 chunks per retriever before fusion.
- Relevance unit: a section (self-made) or an abstract (SciFact). A chunk that spans two sections counts for both. Chunk rankings map to unit rankings by first appearance.
- RRF constant k = 60, the value from Cormack et al. 2009.
- Bootstrap: 1,000 resamples over queries, seed 0, percentile 95% interval.
- Peak memory: process VmRSS sampled every 20 ms by a watchdog thread. The peak covers the whole process, not only the run's own allocations.
- ONNX Runtime CPU memory arena turned off (`enable_cpu_mem_arena=False`). With the arena on, RSS passed 2 GB on the first dense run. With it off, the peak was 394 MB.
- Default grid threads: 4 (the whole VM), pinned with `taskset -c 0-3`. The tiny grid is timed on 2 cores with `taskset -c 0,1`, as Done-means item 1 asks.
- TDD: the core modules (corpus, chunkers, BM25, metrics, grid) were written before their tests in this run. The guards (network guard, resume test, memory guard) were each checked by breaking the code and watching the test fail. Later features follow test first.
- Social preview PNG: drawn by a pure Python script with a built-in pixel font, so no image library is needed.
- gitleaks: one allowlisted path, the FastAPI JWT tutorial, which holds the public sample token from the FastAPI docs. Options: drop the file or allowlist it. It is a real doc section and the token is a published example.
- Run order: every BM25 run goes first, before any model is loaded, then dense and hybrid one chunk setting at a time. Peak RAM is reset at the start of each run. A hybrid run reuses the dense run's vectors, so its peak is the larger of its own peak and that embedding peak. Each row also records `rss_start_mb`. This came from the code review: the first pass reset the peak once per chunk setting, so later runs inherited earlier peaks.
- Code review fixes before the final grid: stable tie order in `top_k`, one row per run id in the report, a journal path that works for any file name, healing of a half-written last line, a lock in the memory guard, no made-up zeros for empty groups, and table cells written with textContent. The first-pass results were set aside in `logs/first-pass/` (not committed) and the whole grid was rerun.
- Tiny grid timing: 0.43 s wall time for 36 runs with `taskset -c 0,1` on 2026-11-20, while the default grid used the other cores.
