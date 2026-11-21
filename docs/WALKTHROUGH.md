# Walkthrough

This is a tour of every file. Short sentences. One idea each.

## The big picture

The lab answers one question. Which retrieval settings work best on a small CPU?
It loads documents. It cuts them into chunks. It builds a search index. It runs every query.
It scores the answers. It writes one line of results per setting.
Then a script turns those lines into tables, a guide and a web page.

## Top level files

- `README.md`: the front page. The tables inside the `BEGIN` and `END` comments are written by a script.
- `CLAUDE.md`: tells an AI agent what to read first.
- `PROJECT_CONTEXT.md`: a one-page summary for an agent or a new reader.
- `PROGRESS.md`: what is done and what is next.
- `BLOCKERS.md`: what failed, the exact error, and what was done instead.
- `DECISIONS.md`: every choice, the options, and the reason.
- `feature_list.json`: the list of features, the commands that prove each one, and a pass flag.
- `init.sh`: one command. It makes a virtual environment, installs the project, lints it, checks links and runs the tests.
- `pyproject.toml`: the package name, the dependencies and the `cpu-rag-lab` command.
- `models.json`: the embedding models. Each one has a size, a license, a download URL and file hashes.
- `LICENSE`: MIT.
- `CHANGELOG.md`: what changed in each release.
- `CONTRIBUTING.md`: the short rules for helping.
- `.gitleaks.toml` and `.pre-commit-config.yaml`: the secret scan.
- `.env.example`: shows that no key is needed.

## The package: `src/cpu_rag_lab/`

- `corpus.py`: loads a corpus. A corpus has documents, and each document has sections. A section is what a query is judged against. It parses Markdown into sections at headings. It drops code blocks. It turns good headings into queries. It also loads SciFact and the tiny toy corpus.
- `tiny.md`: the toy corpus. Eight short how-to sections. Tests use it, so they need no download.
- `chunkers.py`: three ways to cut a document. `fixed` takes a window of N words and slides it. `sentence` packs whole sentences up to N words. `heading` keeps each section apart and splits long ones by sentence. Every chunk remembers which sections its words came from.
- `bm25.py`: the BM25 word-match score, written from scratch with numpy. It keeps an inverted index: for each word, the chunks that hold it and a precomputed score.
- `embedders.py`: turns text into vectors. `HashEmbedder` is a fake. It hashes words into buckets, so tests run with no model. `FastEmbedder` runs a real model through FastEmbed on the CPU. Both work in batches of 32.
- `retrieve.py`: dense search is a dot product between the query vector and every chunk vector. Hybrid search merges the BM25 list and the dense list with reciprocal rank fusion. `to_units` turns a list of chunks into a list of sections, keeping the first time each section shows up.
- `metrics.py`: Recall@5, Recall@10, MRR@10 and nDCG@10 for one query. Then a bootstrap: resample the queries many times and take the middle 95% of the means.
- `memguard.py`: a small thread reads the process memory from `/proc/self/status` every 20 ms. It keeps the peak. If memory goes over the limit, the next check stops the run.
- `grid.py`: the grid runner. It lists every setting from a config file. It skips settings that are already done. It runs every BM25 setting first, before a model is loaded, then dense and hybrid. It resets the memory peak at the start of each run. It writes a journal line when a run starts and a result line when it ends. If the program stops in the middle, the journal shows a run that started but never ended. That run goes back to the queue.
- `report.py`: reads `results.jsonl` and writes the README tables, `docs/DECISION_GUIDE.md`, `docs/index.html` and `results/summary.json`. Every number goes through a `Facts` object, which remembers it. The tests use that list to prove nothing was typed by hand.
- `svg.py`: draws bar charts and scatter plots as plain SVG text.
- `cli.py`: the `cpu-rag-lab` command with `run`, `status` and `report`.

## Configs: `configs/`

- `tiny.json`: the toy corpus, the hash embedder, small chunk sizes. It runs in under a second.
- `default.json`: the real grid. Self-made docs with all three chunkers, and the SciFact pool with two chunkers. Sizes 128, 256 and 512 words. Overlap 0 and 20 percent. BM25, dense and hybrid.

## Data: `data/`

- `selfmade/raw/`: Markdown docs from FastAPI, uv and HTTPX, fetched at pinned commits.
- `selfmade/manifest.json`: for each file, the repo, the commit, the path, the license and a SHA-256.
- `selfmade/licenses/`: a copy of each repo's license.
- `scifact/`: downloaded by `scripts/fetch_data.py`. Not committed.

## Results: `results/`

- `results.jsonl`: one line per run of the default grid. It holds the setting, the scores with intervals, latency, peak memory, build time, the date, the CPU and the seed.
- `results.state.jsonl`: the journal. Not committed.
- `tiny.jsonl`: the tiny grid.
- `summary.json`: totals for the default grid.

## Scripts: `scripts/`

- `fetch_data.py`: downloads the self-made docs, SciFact and the model. It checks every hash.
- `check_links.py`: checks every relative link and anchor in the Markdown and HTML files.
- `make_social_preview.py`: draws the 1280 by 640 social preview with a tiny built-in pixel font.

## Tests: `tests/`

- `conftest.py`: blocks any network connection that is not local. Every test runs with it.
- `test_network_guard.py`: proves the guard blocks a remote host and allows localhost.
- `test_corpus.py`, `test_chunkers.py`, `test_bm25.py`, `test_metrics.py`, `test_retrieve.py`, `test_memguard.py`: one file per module.
- `test_grid.py`: runs a small grid, stops it in the middle of a chunk setting, fakes a hard kill, resumes, and checks that every run is done once.
- `test_report.py`: rebuilds the README and the guide from `results.jsonl` and checks that every number in them came from that file.

## Docs: `docs/`

- `index.html`: the results site. It opens from disk. The data sits inside the page.
- `DECISION_GUIDE.md`: the takeaways, written by the report script.
- `DEMO.md`: a real terminal session.
- `INTERVIEW_QA.md`: questions a founder might ask, with answers tied to code and results.
- `PLAN.md`, `ENVIRONMENT.md`, `TOOLING.md`, `RELEASE_CHECK.md`: how the build went.
- `HUMAN_STEPS.md`: the steps only Shreyas can do.
- `handoff/COWORK_PROMPT.md`: a prompt for the browser steps.
- `build/BUILD_PROMPT.md`: the full brief the agents worked from.
- `topics.txt`, `GITHUB_ABOUT.md`, `social-preview.png`: GitHub page settings.

## CI: `.github/`

- `workflows/ci.yml`: on each push and pull request it runs `init.sh`, checks that generated files are fresh and runs the tiny grid.
- `workflows/grid.yml`: runs the default grid only when started by hand.
- `ISSUE_TEMPLATE/`: forms for bugs and new settings.
