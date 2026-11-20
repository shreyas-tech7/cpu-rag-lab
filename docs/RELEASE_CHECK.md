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
