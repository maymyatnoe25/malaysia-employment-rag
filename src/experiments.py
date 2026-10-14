import argparse
import json
from pathlib import Path

from src.evaluate import first_gold_rank, load_questions, summarize
from src.retrieve import Retriever
from src.search import load_sections, make_units

MODES = ("bm25", "dense", "hybrid")
OUT = Path("eval/results_dev.json")


def score(units, model, questions):
    retriever = Retriever(units, model)
    result = {}
    for mode in MODES:
        ranks = []
        for q in questions:
            ranked = [u["section_id"] for u, _ in retriever.search(q["question"], mode, k=20)]
            ranks.append(first_gold_rank(ranked, q["gold"]))
        result[mode] = summarize(ranks)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="0,600,1200", help="unit sizes, 0 = whole sections")
    ap.add_argument("--models", default="minilm,bge-small")
    args = ap.parse_args()

    sections = load_sections()
    questions = [q for q in load_questions()
                 if q["kind"] == "answer" and q["split"] == "dev"]
    print(f"{len(questions)} dev questions (one question = {100/len(questions):.1f} points)\n")

    rows = []
    for size in [int(s) for s in args.sizes.split(",")]:
        units = make_units(sections, max_chars=size or None)
        for model in args.models.split(","):
            res = score(units, model, questions)
            for mode in MODES:
                rows.append({"unit_size": size, "units": len(units), "model": model,
                             "mode": mode, **res[mode]})

    print(f"{'size':>5s} {'units':>5s} {'model':10s} {'mode':7s} "
          f"{'hit@1':>6s} {'hit@3':>6s} {'hit@5':>6s} {'MRR':>6s}")
    for r in rows:
        print(f"{r['unit_size']:5d} {r['units']:5d} {r['model']:10s} {r['mode']:7s} "
              f"{r['hit@1']:6.2f} {r['hit@3']:6.2f} {r['hit@5']:6.2f} {r['mrr']:6.2f}")

    OUT.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("\nSaved", OUT)


if __name__ == "__main__":
    main()
    