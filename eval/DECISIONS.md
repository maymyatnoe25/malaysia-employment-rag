# Decisions made on the dev set (before looking at test results)

- Unit size: 1200 characters
- Embedding model: all-MiniLM-L6-v2 (minilm)
- Retrieval: hybrid (BM25 + embeddings, reciprocal rank fusion)
- Reranker: not used (hurt hit@1 and MRR on dev at both unit sizes)

Note: one early test table (bge-small, 1200, hybrid) was seen before tuning.
No decision was made from it.
## Answer generation: how the model is chosen
Priority 1: do not give a confident answer to a question the Act does not cover.
Priority 2: among models that do that, prefer more correct answers on answerable questions.
Chosen on the 35 dev questions only. Test split run once afterwards.
## Generator chosen on dev
llama3.2 with the v3 prompt and fuzzy quote check (0 of 9 unanswerable questions answered
as if covered, per the priority rule above). gemma3:4b answered 2 of 9 as if covered.
Both models gave wrong answers on answerable questions (hand-graded). The app shows
sources and the verbatim quote first, with the summary labelled machine-generated.