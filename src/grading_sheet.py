import json
from pathlib import Path

from src.search import load_sections

rows = [json.loads(line) for line in
        Path("eval/generations_test_v3_test.jsonl").read_text(encoding="utf-8").splitlines()]
sections = {s["id"]: s for s in load_sections()}

out = []
for r in rows:
    out.append("=" * 78)
    out.append(f"{r['id']}  [{r['kind']}]   gold={r['gold']}   retrieved={r['retrieved']}")
    if r["kind"] == "answer":
        got = bool(set(r["gold"]) & set(r["retrieved"]))
        out.append(f"correct section retrieved: {'YES' if got else 'NO'}")
    out.append(f"QUESTION: {r['question']}")
    out.append(f"MODEL:    {r['answer']}")
    if r["quote"]:
        out.append(f"QUOTE:    {r['quote'][:300]}")
    for g in r["gold"]:
        s = sections.get(g)
        if s:
            out.append(f"--- THE ACT, {g} ({s['heading']}) ---")
            out.append(s["body"][:1500])
    out.append("YOUR GRADE: ")
    out.append("")
Path("eval/grading_test.txt").write_text("\n".join(out), encoding="utf-8")
print("Wrote eval/grading_test.txt with", len(rows), "questions")