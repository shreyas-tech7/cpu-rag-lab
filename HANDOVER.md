# Handover

## State
The build is finished as a release candidate on branch `claude/build-cpu-rag-lab`. Every Done-means item is true, with one note: the default grid took 24.5 minutes instead of about 20. Dense search uses all-MiniLM-L6-v2 because Hugging Face was blocked, and the optional reranker is off.

## Next
1. Follow `docs/HUMAN_STEPS.md`: create `main` from `5ad5fba`, open the pull request, merge with a merge commit, tag `v0.1.0-rc1` on the release SHA in `CHANGELOG.md`.

## Open decisions
- Keep `docs/build/BUILD_PROMPT.md` public or not.
- Which item in `docs/PROPOSALS.md` to build next. bge-small is the obvious first.

## Commands
```bash
./init.sh
.venv/bin/cpu-rag-lab status --config configs/default.json
.venv/bin/cpu-rag-lab report --check
.venv/bin/cpu-rag-lab run --config configs/tiny.json --results /tmp/tiny.jsonl
```
