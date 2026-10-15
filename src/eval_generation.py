import argparse
import json
from pathlib import Path

from src.evaluate import load_questions
from src.generate import Assistant


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "test"])
    ap.add_argument("--limit", type=int, default=0, help="only the first N questions")
    args = ap.parse_args()

    questions = [q for q in load_questions() if q["split"] == args.split]
    if args.limit:
        questions = questions[:args.limit]
    assistant = Assistant()

    rows = []
    for i, q in enumerate(questions, start=1):
        r = assistant.answer(q["question"])
        r.update(id=q["id"], kind=q["kind"], gold=q["gold"])
        rows.append(r)
        print(f"{i}/{len(questions)} {q['id']}", flush=True)

    out = Path(f"eval/generations_{args.split}")
    out.with_suffix(".jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    with out.with_suffix(".txt").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(f"{r['id']} [{r['kind']}] gold={r['gold']}\n")
            f.write(f"Q: {r['question']}\nA: {r['answer']}\n")
            f.write(f"retrieved={r['retrieved']} cited={r['cited']}\n\n")

    ans = [r for r in rows if r["kind"] == "answer"]
    none = [r for r in rows if r["kind"] == "none"]
    print(f"\n=== {args.split}: answerable ({len(ans)}) ===")
    print("gold section retrieved in top 3 :", sum(1 for r in ans if set(r["gold"]) & set(r["retrieved"])))
    print("model abstained (bad)           :", sum(1 for r in ans if r["abstained"]))
    print("cites a gold section            :", sum(1 for r in ans if set(r["gold"]) & set(r["cited"])))
    print("cites a section it was not given:", sum(1 for r in ans if set(r["cited"]) - set(r["retrieved"])))
    print("no citation at all (not abstain):", sum(1 for r in ans if not r["cited"] and not r["abstained"]))
    print(f"\n=== {args.split}: not in the Act ({len(none)}) ===")
    print("correctly abstained             :", sum(1 for r in none if r["abstained"]))
    print("answered anyway (bad)           :", sum(1 for r in none if not r["abstained"]))


if __name__ == "__main__":
    main()