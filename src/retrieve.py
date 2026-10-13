import hashlib
import sys
from pathlib import Path

import numpy as np

from src.search import BM25Index, load_sections, make_units

CACHE = Path("data/processed")

# name on Hugging Face, and the prefix this model expects before a question
MODELS = {
    "minilm": ("sentence-transformers/all-MiniLM-L6-v2", ""),
    "bge-small": ("BAAI/bge-small-en-v1.5",
                  "Represent this sentence for searching relevant passages: "),
}


def rank_positions(scores):
    """1 = best. Turns scores into ranks."""
    order = np.argsort(-scores)
    ranks = np.empty(len(scores), dtype=int)
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks


def top_sections(units, scores, k):
    """Best-scoring unit per section, top k sections."""
    seen, out = set(), []
    for i in np.argsort(-scores):
        u = units[i]
        if u["section_id"] in seen:
            continue
        seen.add(u["section_id"])
        out.append((u, float(scores[i])))
        if len(out) == k:
            break
    return out


class DenseIndex:
    def __init__(self, units, model_key="bge-small"):
        from sentence_transformers import SentenceTransformer
        name, self.prefix = MODELS[model_key]
        self.model = SentenceTransformer(name)
        key = hashlib.md5("\n".join(u["text"] for u in units).encode()).hexdigest()[:10]
        cache = CACHE / f"emb_{model_key}_{key}.npy"
        if cache.exists():
            self.emb = np.load(cache)
        else:
            self.emb = self.model.encode(
                [u["text"] for u in units], batch_size=32,
                normalize_embeddings=True, show_progress_bar=True)
            np.save(cache, self.emb)

    def scores(self, query):
        q = self.model.encode([self.prefix + query], normalize_embeddings=True)[0]
        return self.emb @ q


class Retriever:
    def __init__(self, units, model_key="bge-small"):
        self.units = units
        self.bm25 = BM25Index(units)
        self.dense = DenseIndex(units, model_key)

    def scores(self, query, mode="hybrid"):
        if mode == "bm25":
            return np.asarray(self.bm25.scores(query))
        if mode == "dense":
            return self.dense.scores(query)
        rb = rank_positions(np.asarray(self.bm25.scores(query)))
        rd = rank_positions(self.dense.scores(query))
        return 1 / (60 + rb) + 1 / (60 + rd)

    def search(self, query, mode="hybrid", k=5):
        return top_sections(self.units, self.scores(query, mode), k)


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m src.retrieve "your question"')
    query = " ".join(sys.argv[1:])
    retriever = Retriever(make_units(load_sections()))
    print("Question:", query)
    for mode in ("bm25", "dense", "hybrid"):
        hits = retriever.search(query, mode, k=3)
        print(f"{mode:7s}", " | ".join(f"{u['section_id']} ({u['heading'][:28]})"
                                       for u, _ in hits))


if __name__ == "__main__":
    main()