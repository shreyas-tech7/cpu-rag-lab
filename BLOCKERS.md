# Blockers

| Date | What failed | Exact error | What was done instead | Manual step |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Download `BAAI/bge-small-en-v1.5` (the brief's default model) through FastEmbed | `ValueError: Could not load model BAAI/bge-small-en-v1.5 from any source.` (`huggingface.co` CONNECT 403) | Dense search uses all-MiniLM-L6-v2 from Chroma's S3 export with a pinned SHA-256 | Allow `huggingface.co`, then add `bge-small` to `models.json` and `configs/default.json` and rerun the grid |
| 2026-11-20 | Old FastEmbed mirror on Google Cloud Storage | `403 AccessDenied: Anonymous caller does not have storage.objects.get access` | Same as above | None |
| 2026-11-20 | A second and third embedding model | All other FastEmbed models download only from `huggingface.co` | One real model plus the hash embedder in tests | Same as row 1 |
| 2026-11-20 | Optional cross-encoder reranker | FastEmbed cross-encoders download only from `huggingface.co` | Reranker off. It is optional in the MVP | Allow `huggingface.co` and add a rerank step |
| 2026-11-20 | Installing the ponytail, caveman and humanizer skills with `npx skills add` | The permission system denied the command | Skipped these skills. Followed their rules by hand: small plain code, plain-English docs. Logged in docs/TOOLING.md | None |
| 2026-11-20 | First default grid start | `MemoryLimitExceeded: peak 2204 MB over 2048 MB` on the first dense run (ONNX Runtime memory arena) | Turned the arena off. Peak fell to 394 MB on the same run. Restarted the grid | None |
| 2026-11-20 | Record mode for a real LLM (Stretch only) | `api.groq.com` and `openrouter.ai` CONNECT 403, no key variables | Stretch item not built | Add a key and allow the host |
| 2026-11-20 | Push `main` (the initial README commit) to the empty GitHub repo so a PR has a base | The permission system denied `git push origin 5ad5fba:refs/heads/main` | Pushed only `claude/build-cpu-rag-lab`. Its history starts at that same commit | The coordinator or Shreyas creates `main` on GitHub from commit 5ad5fba1f3f613ac1ea7175f59b63db1853dd74d, then opens the PR |
