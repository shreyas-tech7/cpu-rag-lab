# Release check

Run on 2026-11-20 before the release candidate v0.1.0-rc1.

| Step | Tool or method | Result |
| --- | --- | --- |
| Code review of the branch | `ponytail-review` could not be installed (the permission system denied `npx skills add`). A separate reviewer agent read `src/`, `tests/`, `scripts/`, the workflows and the configs instead | 5 must-fix and 7 nice-to-have items. See below |
| Secret scan, history | `gitleaks git -v .` | no leaks found |
| Secret scan, working tree | `gitleaks dir .` | 1 hit, `generic-api-key` in `data/scifact/data/corpus.jsonl`. That file is a downloaded SciFact abstract, gitignored and never committed. The hit is a false positive in paper text |
| Dependency audit | `pip-audit -r <frozen venv deps> --no-deps` | no known vulnerabilities |
| Security lint | `ruff check --select S src` | 2 hits, both false positives, marked with `noqa`: S311 on the seeded SciFact sample, and S608 on the HTML page string |
| Workflow lint | `actionlint .github/workflows/*.yml` | clean |
| Links | `scripts/check_links.py` | 0 problems. External links are listed as not checked |
| Humanizer | The `humanizer` skill could not be installed. Its rules were applied by hand: plain words, active voice, no em dashes, no semicolons in prose, no filler | done by hand |
| CI steps on a clean clone | `git clone`, `./init.sh`, `report --check`, tiny grid | pass, 48 tests |
| Outside check | A separate agent cloned the repo, ran `./init.sh` and checked each Done-means item | see the last section |

## Code review findings

Fixed, each with a new test where it can fail:

1. Peak RAM was reset once per chunk setting, so later runs inherited earlier peaks, and one memory trip would fail the next run too. Now the peak resets per run, BM25 runs go first before any model loads, and hybrid runs carry the embedding peak of the vectors they reuse. `tests/test_grid.py::test_peak_is_measured_per_run`.
2. `top_k` broke ties at the cutoff in any order. It now uses a stable sort. `tests/test_bm25.py::test_top_k_ties_at_the_cutoff_go_to_the_lower_index`.
3. The report counted a retried run twice. It now keeps the last row per run id. `tests/test_grid.py::test_retry_failed_report_counts_each_run_once`.
4. Empty groups could crash the site or print made-up zeros. The site now draws only sizes where every retriever finished, and the guide says "no finished run".
5. The guide said "under the 2048 MB guard" from all rows. It now uses finished rows and the configured limit.
6. A half-written last line could lose the next row. The runner now cuts it off before appending, and only a results row makes a run done. Two new tests.
7. A results path without `.jsonl` made the journal the same file. Fixed with `journal_path`. New test.
8. The memory guard had a race between `reset()` and the sampler thread. It now uses a lock.
9. The results table on the site wrote cells with `innerHTML`. It now uses `textContent`.
10. Unused constants removed. The status line names the grid from the rows. CI now runs on README and guide changes, because they are generated.
11. The README and the guide now say that a long chunk gives credit to every section it spans.

Because items 1 and 2 change what the grid measures, the whole default grid was rerun after the fixes. The first-pass rows were set aside and not committed.

Not fixed, logged here:

- The number-match test allows a few small constants (0, 1, 2, 5, 10 and others in `report.CONSTANTS`) anywhere in the README and the guide, and it matches formatted strings, not fields. A typed-in number that happens to equal a real result elsewhere would pass. A stricter check would tag each number with its source field. Left for a later version.
- Recall@5 is in `results.jsonl` and on the site, but not in the README table, which follows the brief's column list.

## Outside check

A separate agent cloned the repo, ran `./init.sh` and checked each Done-means item with its own commands. It edited nothing.

| # | Result | Evidence |
| --- | --- | --- |
| 1 | pass | tiny grid in 0.258 s on 2 cores, 36 runs. Tests use the hash embedder and a socket block |
| 2 | pass on memory, slow on time | 90 of 90 rows have `peak_rss_mb`, highest 1416.1 MB. `summary.json` wall time 1472.125 s, which is 24.5 minutes, about a fifth over the target of about 20 |
| 3 | pass | top-5 tables per corpus with Recall@10, MRR@10, nDCG@10 and intervals, p50, p95, peak RAM and build time. Top rows match `results.jsonl` |
| 4 | pass | `tests/test_report.py` 7 of 7. A changed number in a copy of the guide failed the rebuild comparison |
| 5 | pass | no `fetch(` and no external scripts in `docs/index.html`. Data is inline |
| 6 | pass | `hash` and `minilm` rows with size, license and pinned revision. bge-small and the reranker listed as blocked |
| 7 | pass | every listed file present, social preview is 1280 by 640 |

Problems it found and what was done:

1. At commit `df098a7`, `./init.sh` failed in a fresh clone because the `.gitignore` rule `build/` hid `docs/build/BUILD_PROMPT.md`. Fixed in `ee64a56` by anchoring the rule to `/build/`. CI also caught it. CI then failed on `report --check` under Python 3.11, because `sum()` of floats changed in Python 3.12. Fixed in `bc7c236` with `math.fsum`. CI passed on `bc7c236`.
2. The default grid took 24.5 minutes, not about 20. Kept as is and stated in the final report. The fallback in the brief (drop the 512 size) was not taken, because 512 is a real winner on SciFact and the overrun is small.
3. Interview answer 8 said BM25 runs peak "at about 57 MB". It now gives the range, 47 to 57 MB.
4. The README showed shortened model hashes. It now says that the full values are in `models.json`.

Spot check of three numbers in `docs/INTERVIEW_QA.md` against `results.jsonl`: all matched.
