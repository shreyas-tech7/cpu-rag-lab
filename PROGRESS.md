# Progress

## Done
- Library, CLI, tests (48, offline), CI (green on Python 3.11), generated README, decision guide and site.
- Default grid: 90 of 90 runs, 0 failed, 24.5 minutes of run time on a 4-core VM, peak 1,416 MB (`results/summary.json`). Tiny grid: 36 runs in under a second on 2 cores.
- Code review fixes with tests, then a full rerun of the grid.
- Study-later kit, DEMO, CHANGELOG, HUMAN_STEPS, COWORK_PROMPT, PROPOSALS, RELEASE_CHECK.
- Release check and outside check done. See `docs/RELEASE_CHECK.md`.
- Release SHA written into CHANGELOG.md and docs/HUMAN_STEPS.md by a follow-up commit.

## Next
- Shreyas: the steps in `docs/HUMAN_STEPS.md`, starting with creating `main` and opening the pull request.

## Open blockers
See BLOCKERS.md: Hugging Face blocked (bge-small and reranker), skill installs denied, push of main denied, record mode has no key.

## Last init.sh
2026-11-20 06:10 UTC: all checks passed, 48 tests.
