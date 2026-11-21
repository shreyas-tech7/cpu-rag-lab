# Contributing

Thanks for helping. This is a small lab, so the rules are short.

1. Run `./init.sh` before and after your change. It installs the project, lints it, checks links and runs every test offline.
2. Write a test that fails first, then the code that makes it pass. Name the broken case in the test docstring.
3. Never type a result number into the README or the decision guide. Change `results/results.jsonl` by running the grid, then run `cpu-rag-lab report`.
4. Never change a test, a reference value or the query set to make code pass. If a test is wrong, show why in the pull request.
5. Keep secrets out. The pre-commit hook runs gitleaks. No key is needed to run the lab.
6. New models must be free, CPU-friendly and pinned in `models.json` with a file hash and a license.

To add an embedding model, add an entry to `models.json` with its URL and hashes, add its name to `configs/default.json`, run `python scripts/fetch_data.py models`, then rerun the grid.
