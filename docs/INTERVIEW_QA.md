# Interview questions and answers

Each answer points to the code and to a results file. Numbers come from `results/results.jsonl` (default grid of 90 runs, run on 2026-11-20 on a 4-core VM, model all-MiniLM-L6-v2, bootstrap seed 0). "selfmade" is the corpus of FastAPI, uv and HTTPX docs with 574 heading queries. "scifact1000" is a 1,000-abstract SciFact pool with 300 claims.

## 1. What does this project do, in one breath?

It runs one grid of retrieval settings on a plain CPU and scores each one. The settings are chunker, chunk size, overlap and retriever. Each run writes one JSON line with quality, intervals, latency, memory and build time. A script then writes the README tables, a decision guide and a static site from those lines. See `src/cpu_rag_lab/grid.py` (`Runner.run`) and `src/cpu_rag_lab/report.py` (`build`).

## 2. What does reciprocal rank fusion do?

It merges two ranked lists without looking at their scores. Each chunk gets the sum of 1 / (60 + rank) over the lists it appears in, and the merged list sorts by that sum. BM25 scores and cosine scores live on different scales, so adding them would need tuning. Ranks need none. The code is `rrf` in `src/cpu_rag_lab/retrieve.py`, with `RRF_K = 60` and a depth of 100 chunks per list. On selfmade, hybrid search with the heading chunker at 512 words reached nDCG@10 0.614 [0.582, 0.645]. BM25 alone reached 0.568 and dense alone 0.530 for the same chunks. The two lists miss different sections, so the merge finds more of them.

## 3. Why intervals over queries?

A mean over a few hundred queries moves when you swap in other queries. Without an interval, a gap of 0.01 looks like a win. The bootstrap resamples the queries with replacement 1000 times and keeps the middle 95% of the means. See `bootstrap_ci` in `src/cpu_rag_lab/metrics.py`. On selfmade, hybrid heading at 128, 256 and 512 words scored 0.613, 0.613 and 0.614. Their intervals overlap almost fully, so the data does not pick a size there. The decision guide lists these as close calls: every setting whose mean falls inside the best setting's interval. Then it names the fastest of them.

## 4. How does chunk size change recall and latency?

Smaller chunks won on selfmade for the fixed and sentence chunkers. With sentence chunks and BM25, Recall@10 fell from 0.756 at 128 words to 0.692 at 256 and 0.652 at 512. Small chunks hold one topic, so the right section is not diluted by its neighbors. Query latency barely moved, because search cost is small next to embedding the query. Index build time fell with size: dense search took 33.5 s to embed 719 sentence chunks at 128 words and 11.5 s for 202 chunks at 512. Fewer chunks means fewer model calls. MiniLM also cuts input at 256 tokens, so a 512-word chunk loses its tail for dense search.

## 5. Why are the self-made queries only a proxy?

They are section headings, and the right answer is the section under the heading. Real users do not type headings. Headings are short and reuse the words of the docs, which helps BM25. So the scores show which settings find a named section. They do not show how a real question would fare. `queries_from_headings` in `src/cpu_rag_lab/corpus.py` drops generic headings like "Recap", one-word headings and sections under 30 words, and the heading text is removed from the body so the query does not match itself.

## 6. Why did the heading chunker win on selfmade?

Its chunks line up with the units that queries are judged against. A heading chunk never mixes two sections, so a hit is clean. That is also a warning: the task rewards chunks shaped like its answers. SciFact has no headings. Each abstract is one section, so the heading chunker would repeat the sentence chunker there, and it is left out. On SciFact the chunkers tie: mean nDCG@10 0.797 for fixed and 0.798 for sentence. See `heading` in `src/cpu_rag_lab/chunkers.py` and the per-corpus axes in `configs/default.json`.

## 7. How do you map chunks back to answers?

Every chunk keeps the ids of the sections its words came from. `to_units` in `src/cpu_rag_lab/retrieve.py` walks the ranked chunks and keeps each section the first time it appears. Metrics then score the section list. This lets different chunkers compete on the same answer key.

## 8. How do you keep memory under 2 GB?

A watchdog thread in `src/cpu_rag_lab/memguard.py` reads `VmRSS` from `/proc/self/status` every 20 ms and keeps the peak. The runner calls `check()` after each embedding batch of 32 and stops the run if the peak passed 2048 MB. The first real run hit 2,204 MB because ONNX Runtime's memory arena kept growing on mixed batch shapes. Turning the arena off (`enable_cpu_mem_arena=False` in `src/cpu_rag_lab/embedders.py`) fixed it. The highest peak in the final grid was 1,416 MB (`results/summary.json`). The peak resets at the start of each run. BM25 runs go first, before the model is loaded, so they peak between 47 and 57 MB on selfmade. The guard has its own tests with a limit of 1 MB in `tests/test_grid.py`.

## 9. What happens if the grid dies halfway?

The runner writes a journal line when a run starts and a result line when it ends, with an fsync each time. On restart, `states()` in `src/cpu_rag_lab/grid.py` reads both files. A run that started but never ended goes back to pending. Finished runs are skipped. `tests/test_grid.py` stops a grid in the middle of a chunk setting, fakes a hard kill and checks that every run ends up done exactly once.

## 10. Why write BM25 from scratch?

The brief asked for it, and it keeps the stack to numpy. It is about 60 lines in `src/cpu_rag_lab/bm25.py` with k1 = 1.2 and b = 0.75. It builds an inverted index of precomputed term weights, so a query only touches the chunks that share a word with it. On selfmade a BM25 query takes about 0.03 ms at the median, roughly 60 times faster than a dense query (1.86 ms median p50 in the README cost table).

## 11. Is dense search worth it on a CPU?

It depends on the queries. On selfmade, dense search scored below BM25 in all 18 matching settings. The heading queries reuse the docs' own words, which suits BM25. On SciFact, where the queries are real claims, dense beat BM25 in all 12 matching settings. In both corpora the interval of the best dense setting overlaps the interval of the best BM25 setting, so neither win is sure. Dense costs about a minute of embedding per SciFact index and about 1.4 GB of memory, against a fraction of a second and under 100 MB for BM25. Hybrid search had the best mean on both corpora. See the cost table in the README.

## 12. Why MiniLM and not bge-small?

The brief's default was `BAAI/bge-small-en-v1.5`. FastEmbed 0.9.1 downloads it only from huggingface.co, which answered 403 on the build machine, and the old Google Cloud Storage mirror answered AccessDenied. A Chroma export of all-MiniLM-L6-v2 on S3 was reachable. Its archive and model file hashes are pinned in `models.json`, and `scripts/fetch_data.py` checks them. `BLOCKERS.md` has the details. The reranker is off for the same reason.

## 13. How do you know the README numbers are real?

Nobody types them. `report.py` formats every number through a `Facts` object that records it. `tests/test_report.py` rebuilds the README blocks and the decision guide from `results.jsonl` and checks that every number in them is a recorded fact or a known constant like 95 or 1000. CI runs `cpu-rag-lab report --check`, which fails if the committed files differ from a fresh build.

## 14. How do tests run without a model or the network?

`HashEmbedder` in `src/cpu_rag_lab/embedders.py` hashes word unigrams and bigrams into 384 signed buckets. Texts that share words get close vectors, which is enough to test the dense and hybrid code paths. `tests/conftest.py` blocks every socket to a non-local host, and `tests/test_network_guard.py` proves the block works. The tiny grid in `configs/tiny.json` uses the hash embedder and the built-in toy corpus.

## 15. Why is dense latency on SciFact so uneven?

Dense p50 latency on SciFact sits near 3 ms for the 512-word settings (about 1,000 chunks) and jumps to 8 to 16 ms for the smaller sizes (1,270 to 2,390 chunks). The values fall in steps of about 4 ms. A dot product over 2,000 vectors of 384 numbers takes far less than that. The likely cause is contention between numpy's threads and ONNX Runtime's threads on a 4-core VM. This is an inference, not a measured fact. So read SciFact dense latency as a property of this machine, not of chunk size. Selfmade dense latency stays near 2 ms.

## 16. Why SciFact, and why only part of it?

SciFact is a small public retrieval set from BEIR with expert relevance labels, which makes it a check on the proxy queries. Its 300 dev claims are real questions. Embedding all 5,183 abstracts for every setting took about 80 minutes on this VM, so the default grid uses every cited abstract plus random others up to 1,000, drawn with seed 0. A smaller pool is easier, so these scores sit above published full-pool numbers. `load_scifact` in `src/cpu_rag_lab/corpus.py` builds the pool. Its license is CC BY-NC 2.0, which is fine for a benchmark and is recorded in the README.

## 17. What would you do next?

Rerun with bge-small once Hugging Face is reachable, add the reranker, and build a small set of real user questions for the docs corpus. Each idea is in `docs/PROPOSALS.md` for Shreyas to pick.
