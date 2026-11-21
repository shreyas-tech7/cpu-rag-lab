# Proposals

Ideas that the brief did not ask for. Shreyas picks what gets built.

1. **Rerun with bge-small-en-v1.5.** The brief's default model. It needs huggingface.co, which the build machine could not reach. Add it to `models.json` with its hash and rerun the dense and hybrid rows.
2. **Turn on the cross-encoder reranker.** Same blocker. Rerank the top 20 hybrid chunks and record the added latency, as EncouRAGe did.
3. **Real questions for the docs corpus.** Write 50 to 100 questions a user would ask about FastAPI, uv and HTTPX, with the right section for each. This would test the heading-query proxy directly.
4. **Full SciFact pool.** Run the 5,183-abstract pool as a separate manual grid on a larger machine, to compare with published numbers.
5. **Token-based chunk sizes.** Count model tokens instead of words, so a dense chunk is never cut at 256 tokens.
6. **Answer-quality probe (stretch).** The brief's stretch item: send the same queries and top chunks to a free model in record mode. It needs a provider key, so it waits for Shreyas.
