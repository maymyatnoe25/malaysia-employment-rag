import json
from pathlib import Path

rows = [json.loads(line) for line in
        Path("eval/generations_dev.jsonl").read_text(encoding="utf-8").splitlines()]

out = []


def add(title, items):
    out.append(f"\n##### {title} ({len(items)})\n")
    for r in items:
        out.append(f"{r['id']} gold={r['gold']} retrieved={r['retrieved']} cited={r['cited']}")
        out.append(f"Q: {r['question']}")
        out.append(f"A: {r['answer']}\n")


none = [r for r in rows if r["kind"] == "none"]
ans = [r for r in rows if r["kind"] == "answer"]
add("NOT IN THE ACT but the model answered", [r for r in none if not r["abstained"]])
add("Cited a section it was not given", [r for r in ans if set(r["cited"]) - set(r["retrieved"])])
add("No citation, no refusal", [r for r in ans if not r["cited"] and not r["abstained"]])
add("Gold section retrieved but not cited",
    [r for r in ans if set(r["gold"]) & set(r["retrieved"]) and not set(r["gold"]) & set(r["cited"])
     and r["cited"] and not set(r["cited"]) - set(r["retrieved"])])

Path("eval/problems_dev.txt").write_text("\n".join(out), encoding="utf-8")
print("Wrote eval/problems_dev.txt")