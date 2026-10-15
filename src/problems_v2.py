import json
import re
import sys
from pathlib import Path

tag = sys.argv[1] if len(sys.argv) > 1 else "v2"
rows = [json.loads(line) for line in
        Path(f"eval/generations_dev_{tag}.jsonl").read_text(encoding="utf-8").splitlines()]
ans = [r for r in rows if r["kind"] == "answer"]
none = [r for r in rows if r["kind"] == "none"]

WORDS = re.compile(r"does not (specifically )?(specify|mention|address|contain|provide|say)"
                   r"|not (specified|mentioned|addressed|provided)", re.I)


def in_words(r):
    return (not r["abstained"]) and bool(WORDS.search(r["answer"]))


said_nf = [r for r in ans if r["abstained"] and not r["unsupported"]]
bad_quote = [r for r in ans if r["unsupported"]]
good = [r for r in ans if not r["abstained"]]
print("answerable: answered with verified citation :", len(good))
print("answerable: model said NOT_FOUND            :", len(said_nf))
print("answerable: quote not supported             :", len(bad_quote))
print("not in the Act: refused (NOT_FOUND)         :",
      sum(1 for r in none if r["abstained"] and not r["unsupported"]))
print("not in the Act: said 'does not specify'     :", sum(1 for r in none if in_words(r)))
print("not in the Act: answered as if covered      :",
      sum(1 for r in none if not r["abstained"] and not in_words(r)))

out = []
groups = (("ANSWERED (read these!)", good), ("MODEL SAID NOT_FOUND", said_nf),
          ("QUOTE NOT SUPPORTED", bad_quote),
          ("NOT IN THE ACT, ANSWERED AS IF COVERED",
           [r for r in none if not r["abstained"] and not in_words(r)]))
for title, items in groups:
    out.append(f"\n##### {title} ({len(items)})\n")
    for r in items:
        out.append(f"{r['id']} retrieved={r['retrieved']} cited={r['cited']} support={r['support']}")
        out.append(f"Q: {r['question']}")
        out.append(f"A: {r['answer'][:400]}\nQUOTE: {r['quote'][:250]}\n")
Path(f"eval/problems_dev_{tag}.txt").write_text("\n".join(out), encoding="utf-8")
print(f"Wrote eval/problems_dev_{tag}.txt")