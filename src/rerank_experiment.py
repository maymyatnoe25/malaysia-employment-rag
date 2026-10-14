import argparse

from sentence_transformers import CrossEncoder

from src.evaluate import first_gold_rank, load_questions, summarize
from src.retrieve import Retriever
from src.search import load_sections, make_units

CE_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="1200,600")
    ap.add_argument("--model", default="minilm")
    ap.add_argument("--candidates", type=int, default=20)
    args = ap.parse_args()

    questions = [q for q in load_questions()
                 if q["kind"] == "answer" and q["split"] == "dev"]
    sections = load_sections()
    ce = CrossEncoder(CE_NAME)

    print(f"{len(questions)} dev questions | top {args.candidates} candidates reranked\n")
    print(f"{'size':>5s} {'setup':12s} {'hit@1':>6s} {'hit@3':>6s} {'hit@5':>6s} {'MRR':>6s}")
    for size in [int(s) for s in args.sizes.split(",")]:
        retriever = Retriever(make_units(sections, max_chars=size or None), args.model)
        base, rer = [], []
        for q in questions:
            cands = retriever.search(q["question"], "hybrid", k=args.candidates)
            ids = [u["section_id"] for u, _ in cands]
            base.append(first_gold_rank(ids, q["gold"]))
            scores = ce.predict([(q["question"], u["text"]) for u, _ in cands])
            order = sorted(range(len(cands)), key=lambda i: -scores[i])
            rer.append(first_gold_rank([ids[i] for i in order], q["gold"]))
        for name, ranks in (("hybrid", base), ("+ reranker", rer)):
            s = summarize(ranks)
            print(f"{size:5d} {name:12s} {s['hit@1']:6.2f} {s['hit@3']:6.2f} "
                  f"{s['hit@5']:6.2f} {s['mrr']:6.2f}")


if __name__ == "__main__":
    main()