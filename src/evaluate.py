import argparse
from pathlib import Path

from src.retrieve import Retriever
from src.search import load_sections, make_units
from src.show import norm

QFILE = Path("eval/questions.txt")
MODES = ("bm25", "dense", "hybrid")


def load_questions(path=QFILE):
    qs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|", 4)]
        if len(parts) != 5:
            raise ValueError(f"Bad line (need 5 fields): {line}")
        qid, split, kind, gold, question = parts
        qs.append({"id": qid, "split": split, "kind": kind, "question": question,
                   "gold": [] if gold == "-" else [norm(g) for g in gold.split(",")]})
    return qs


def first_gold_rank(ranked_ids, gold):
    for rank, sid in enumerate(ranked_ids, start=1):
        if sid in gold:
            return rank
    return None


def summarize(ranks):
    n = len(ranks)
    out = {f"hit@{k}": sum(1 for r in ranks if r and r <= k) / n for k in (1, 3, 5)}
    out["mrr"] = sum(1 / r for r in ranks if r) / n
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", type=int, default=1200, help="unit size; 0 = whole sections")
    ap.add_argument("--model", default="bge-small")
    args = ap.parse_args()

    sections = load_sections()
    known = {s["id"] for s in sections}
    questions = [q for q in load_questions() if q["kind"] == "answer"]
    for q in questions:
        for g in q["gold"]:
            if g not in known:
                raise SystemExit(f"{q['id']}: unknown section id {g}")

    units = make_units(sections, max_chars=args.chars or None)
    print(f"{len(units)} units | unit size {args.chars} | model {args.model}\n")
    retriever = Retriever(units, args.model)

    results = {m: {} for m in MODES}
    for q in questions:
        for m in MODES:
            ranked = [u["section_id"] for u, _ in retriever.search(q["question"], m, k=20)]
            results[m][q["id"]] = first_gold_rank(ranked, q["gold"])

    for split in ("dev", "test"):
        qs = [q for q in questions if q["split"] == split]
        if not qs:
            continue
        print(f"=== {split} ({len(qs)} answerable questions) ===")
        print(f"{'mode':8s} {'hit@1':>6s} {'hit@3':>6s} {'hit@5':>6s} {'MRR':>6s}")
        for m in MODES:
            s = summarize([results[m][q["id"]] for q in qs])
            print(f"{m:8s} {s['hit@1']:6.2f} {s['hit@3']:6.2f} {s['hit@5']:6.2f} {s['mrr']:6.2f}")
        print()

    print("=== Misses in the top 3 (dev only, so the test set stays unseen) ===")
    for q in questions:
        if q["split"] != "dev":
            continue
        bad = [m for m in MODES if not (results[m][q["id"]] and results[m][q["id"]] <= 3)]
        if bad:
            print(q["id"], "| gold", q["gold"], "| missed by", bad, "|", q["question"][:60])


if __name__ == "__main__":
    main()