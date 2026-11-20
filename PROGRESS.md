# Progress

## Done
- Initializer: prompt saved, memory files, init.sh, network guard, license, pre-commit gitleaks.
- Library: corpus loaders, three chunkers, BM25, hash and FastEmbed embedders, RRF hybrid, metrics with bootstrap, memory guard, resumable grid runner, report writer, CLI.
- Data: SciFact (hash checked, not committed), self-made corpus (91 docs, committed), MiniLM model (hash checked, not committed).
- Code review fixes: per-run peak RAM with BM25 runs first, stable tie order, one row per run id, any results file name, half-written line healing, guard lock, no made-up zeros, safe table cells. New tests for each.
- Default grid: 90 of 90 runs done, 0 failed, 24.5 minutes of run time, peak 1,416 MB (results/summary.json). Tiny grid: 36 runs in 0.43 s on 2 cores.
- README, decision guide and site generated from results. `report --check` is clean.
- Study-later kit (WALKTHROUGH, INTERVIEW_QA, DECISIONS), DEMO, CHANGELOG, HUMAN_STEPS, COWORK_PROMPT, PROPOSALS.

## In progress
- Release check: outside check, RELEASE_CHECK.md, feature flags.

## Next
- Write the release SHA into CHANGELOG.md and docs/HUMAN_STEPS.md, push, bundle, final report.

## Open blockers
See BLOCKERS.md: Hugging Face blocked (bge-small and reranker), skill installs denied, push of main denied.

## Last init.sh
2026-11-20 06:04 UTC: all checks passed, 48 tests.
