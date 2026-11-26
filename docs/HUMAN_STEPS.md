# Human steps

Steps that only Shreyas can do, in order. The release commit is:

`b98c4e89ba0ebf4cfbfcbbcaa5cdd248d06df3ac`

## 1. Create `main` and open the pull request

The GitHub repo was empty when the build started, and the build machine was not allowed to push `main`. The branch `claude/build-cpu-rag-lab` starts at commit `5ad5fba1f3f613ac1ea7175f59b63db1853dd74d`.

1. Create `main` from that commit. On GitHub: open the branch list and create `main` from `5ad5fba`. Or from a clone:

   ```bash
   git fetch origin
   git push origin 5ad5fba1f3f613ac1ea7175f59b63db1853dd74d:refs/heads/main
   ```

2. Open a pull request from `claude/build-cpu-rag-lab` into `main`: https://github.com/shreyas-tech7/cpu-rag-lab/compare/main...claude/build-cpu-rag-lab
3. Read the diff. Check that the CI run on the pull request passed.
4. Merge with a merge commit, so the release commit stays in the history of `main`.

## 2. Create the tag

```bash
git fetch origin
git tag -a v0.1.0-rc1 b98c4e89ba0ebf4cfbfcbbcaa5cdd248d06df3ac -m "Release candidate 1"
git push origin v0.1.0-rc1
```

Or create a pre-release on GitHub with tag `v0.1.0-rc1` on that commit.

## 3. Run the secret scan once more

```bash
gitleaks git -v .
```

The only allowlisted path is a public sample JWT in the FastAPI docs (`.gitleaks.toml`).

## 4. Check the results yourself

- Read `README.md` and `docs/DECISION_GUIDE.md`.
- Rerun the tiny grid: `./init.sh && .venv/bin/cpu-rag-lab run --config configs/tiny.json`.
- Optional: rerun the default grid on your own machine (see the README).
- Check the model and dataset licenses by hand. Then change the "Human checks, not done yet" list in the README.

## 5. Make the repo public

Done 2026-11-26: the repo is public.

## 6. Turn on Pages

Settings > Pages > Deploy from a branch > `main`, folder `/docs`. The site is `docs/index.html`. Then put the Pages URL in the About box as the website.

## 7. Social preview, About box and topics

- Settings > General > Social preview > upload `docs/social-preview.png`.
- About box description, from `docs/GITHUB_ABOUT.md`:

  Which chunk size and retriever work best on a small CPU? A free, resumable grid with BM25, FastEmbed dense and hybrid search, 95% bootstrap intervals, latency and RAM.

- Topics, from `docs/topics.txt`: rag, retrieval, information-retrieval, bm25, embeddings, fastembed, onnx, cpu, benchmark, chunking, hybrid-search, python.

## 8. Pin the repo

Profile > Customize your pins > select `cpu-rag-lab`. Or list it in the profile README.

## 9. Publish to PyPI

The package name `cpu-rag-lab` was free on PyPI and npm when checked (see `DECISIONS.md`). Use trusted publishing:

1. On https://pypi.org/manage/account/publishing/ add a pending publisher: project `cpu-rag-lab`, owner `shreyas-tech7`, repo `cpu-rag-lab`, workflow `release.yml`.
2. Add a release workflow that builds with `uv build` and uploads with `pypa/gh-action-pypi-publish`. It is not in the repo yet, because publishing waits for you.

## 10. Allow Hugging Face and rerun with bge-small

Hugging Face answered 403 on the build machine (see `BLOCKERS.md`).

1. On a machine that can reach huggingface.co, add `bge-small` to `models.json` with its file hash and to `models` in `configs/default.json`.
2. Rerun: `.venv/bin/cpu-rag-lab run --config configs/default.json`, then `.venv/bin/cpu-rag-lab report`.
3. Optional: add the cross-encoder reranker.

## 11. Record mode (stretch)

The answer-quality probe needs a free provider key and an allowed host. Add the key as a secret, never in a file, then build the probe from `docs/PROPOSALS.md`.

## 12. Decide whether `docs/build/BUILD_PROMPT.md` stays public

It is the full brief the agents worked from. Keep it for transparency or remove it.
