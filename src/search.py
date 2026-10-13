import json
import re
import sys
from pathlib import Path

from rank_bm25 import BM25Okapi

CHUNKS = Path("data/processed/chunks.jsonl")

STOP = set("""a an and are as at be by can do does for from has have how i if in is it
may me my of on or shall so that the their there this to under was what when where
which who will with would you your""".split())


def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def load_sections():
    with CHUNKS.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def split_long(text, max_chars):
    """Cut text into pieces of at most max_chars, preferring '; ' and '. ' breaks."""
    pieces = []
    while len(text) > max_chars:
        cut = max(text.rfind("; ", 0, max_chars), text.rfind(". ", 0, max_chars))
        if cut < max_chars // 2:
            cut = text.rfind(" ", 0, max_chars)
        if cut <= 0:
            cut = max_chars
        pieces.append(text[:cut + 1].strip())
        text = text[cut + 1:].strip()
    if text:
        pieces.append(text)
    return pieces


def make_units(sections, max_chars=1200):
    """Split sections into units of about max_chars. max_chars=None keeps whole sections."""
    units = []
    for s in sections:
        header = (f"Section {s['section']}. {s['heading']}"
                  if s["heading"] else s["section"])
        if not max_chars:
            parts = [s["body"]]
        else:
            parts, group = [], ""
            for para in s["body"].split("\n"):
                for piece in split_long(para, max_chars):
                    if group and len(group) + len(piece) + 1 > max_chars:
                        parts.append(group)
                        group = piece
                    else:
                        group = (group + "\n" + piece) if group else piece
            if group:
                parts.append(group)
        for n, body in enumerate(parts, start=1):
            units.append({
                "unit_id": f"{s['id']}#{n}",
                "section_id": s["id"],
                "section": s["section"],
                "heading": s["heading"],
                "part": s["part"],
                "pages": [s["page_start"], s["page_end"]],
                "text": header + "\n" + body,
            })
    return units


class BM25Index:
    def __init__(self, units):
        self.units = units
        self.bm25 = BM25Okapi([tokenize(u["text"]) for u in units])

    def scores(self, query):
        return self.bm25.get_scores(tokenize(query))

    def search(self, query, k=5):
        """Top-k units, at most one per section (the best unit of each section)."""
        scores = self.scores(query)
        order = sorted(range(len(scores)), key=lambda i: -scores[i])
        seen, results = set(), []
        for i in order:
            u = self.units[i]
            if u["section_id"] in seen:
                continue
            seen.add(u["section_id"])
            results.append((u, float(scores[i])))
            if len(results) == k:
                break
        return results


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m src.search "your question"')
    units = make_units(load_sections())
    print(len(units), "units")
    index = BM25Index(units)
    for rank, (u, score) in enumerate(index.search(" ".join(sys.argv[1:])), start=1):
        snippet = u["text"].split("\n", 1)[-1][:150].replace("\n", " ")
        print(f"{rank}. {u['section_id']} | {u['heading']} | score {score:.1f}")
        print(f"   {snippet}")


if __name__ == "__main__":
    main()