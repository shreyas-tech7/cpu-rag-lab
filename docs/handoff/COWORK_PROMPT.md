# Prompt for Claude Cowork

Paste everything below the line into Claude Cowork.

---

You are helping Shreyas finish the GitHub setup for his private repo https://github.com/shreyas-tech7/cpu-rag-lab. Use the browser, where he is already signed in to GitHub. Work only on that repo.

Do not make the repo public. Do not publish a package. Do not enter any key, token or password. Do not sign in to anything for Shreyas. Do not pay for anything. If a step needs one of these, stop and list it for Shreyas.

Do these steps. Each one is free and can be undone.

1. Open the Actions tab. Report the result of the latest run of the CI workflow on `main` or on `claude/build-cpu-rag-lab`. If it failed, copy the name of the failed step and the last 30 lines of its log.
2. Check that a pull request from `claude/build-cpu-rag-lab` into `main` exists. Report its number and state. Do not merge it.
3. Open Settings > General > Social preview. Upload `docs/social-preview.png` from the repo (download it from the file page first).
4. In the About box (the gear on the repo home page), set the description to:
   Which chunk size and retriever work best on a small CPU? A free, resumable grid with BM25, FastEmbed dense and hybrid search, 95% bootstrap intervals, latency and RAM.
5. In the same box, add these topics: rag, retrieval, information-retrieval, bm25, embeddings, fastembed, onnx, cpu, benchmark, chunking, hybrid-search, python.
6. Open `docs/HUMAN_STEPS.md` in the repo and tell Shreyas which steps are still open.

Finish with a prompt Shreyas can paste into Claude Code. It must hold:

- Context: cpu-rag-lab measures retrieval settings on a CPU. The build is on branch `claude/build-cpu-rag-lab`.
- What is complete: the steps above that you finished.
- What is open: the steps from `docs/HUMAN_STEPS.md` that remain, and anything that failed above.
- This resume launcher, word for word: "Read docs/build/BUILD_PROMPT.md and follow it. Resume from PROGRESS.md on branch claude/build-cpu-rag-lab. Do not ask questions. Do not stop until every Done-means item is true or blocked with a fallback."
