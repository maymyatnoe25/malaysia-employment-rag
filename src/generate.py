import re
import sys

import requests

from src.retrieve import Retriever
from src.search import load_sections, make_units

OLLAMA = "http://localhost:11434/api/generate"
LLM = "llama3.2"
THRESHOLD = 0.8      # share of the quote's 4-word sequences found in a source

PROMPT = """You answer questions about the Malaysian Employment Act 1955 for employees.
Below are numbered sections of the Act. They are the only information you may use.

Reply in exactly this format:
ANSWER: <1 to 3 plain sentences that answer the question>
QUOTE: <words copied exactly from one section below that support the answer>

Rules:
- The QUOTE must be copied word for word from the sections. Never write a section number or the name of the Act as the quote.
- If a section below covers the topic of the question, answer from it.
- Only if no section below contains the answer, reply with the single word NOT_FOUND and nothing else.
- Do not use outside knowledge. Do not guess numbers.

Sections:
{sources}

Question: {question}
"""


def words(s):
    return re.findall(r"[a-z0-9]+", s.lower())


def grams(ws, n=4):
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def support(quote, text):
    """Share of the quote's 4-word sequences that also appear in text."""
    qw = words(quote)
    if len(qw) < 8:
        return 0.0
    qg = grams(qw)
    return len(qg & grams(words(text))) / len(qg) if qg else 0.0


def build_prompt(question, hits, full=None):
    parts = []
    for u, _ in hits:
        text = (full or {}).get(u["section_id"], u["text"])
        parts.append(f"[{u['section_id']}] {text}")
    return PROMPT.format(sources="\n\n".join(parts), question=question)


def ask_llm(prompt, model=LLM):
    r = requests.post(OLLAMA, json={
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0, "num_ctx": 6144}}, timeout=900)
    r.raise_for_status()
    return r.json()["response"].strip()


def parse(raw):
    m = re.search(r"ANSWER:\s*(.*?)\s*QUOTE:\s*(.*)", raw, re.S | re.I)
    if not m:
        return None
    quote = re.split(r"\n\s*ANSWER:", m.group(2), flags=re.I)[0]
    quote = re.sub(r"\[[^\]]*\]", "", quote).strip(" \"'\u201c\u201d\n")
    return m.group(1).strip(), quote


def is_refusal(text):
    return bool(re.search(r"NOT[\s_-]*FOUND", text, re.I))


class Assistant:
    def __init__(self, chars=1200, embed="minilm", k=3, model=LLM, cap=4000):
        units = make_units(load_sections(), max_chars=chars)
        self.retriever = Retriever(units, embed)
        self.k, self.model = k, model
        by_section = {}
        for u in units:
            by_section.setdefault(u["section_id"], []).append(u["text"])
        self.full = {}
        for sid, texts in by_section.items():
            body = texts[0] + "\n" + "\n".join(t.split("\n", 1)[-1] for t in texts[1:])
            self.full[sid] = body[:cap]

    def prompt_for(self, question):
        hits = self.retriever.search(question, "hybrid", k=self.k)
        return hits, build_prompt(question, hits, self.full)

    def answer(self, question):
        hits, prompt = self.prompt_for(question)
        retrieved = [u["section_id"] for u, _ in hits]
        raw = ask_llm(prompt, self.model)
        base = {"question": question, "raw": raw, "retrieved": retrieved,
                "quote": "", "cited": [], "abstained": True, "unsupported": False,
                "support": 0.0, "answer": "NOT_FOUND"}
        parsed = parse(raw)
        if parsed is None:
            base["unsupported"] = not is_refusal(raw)    # broke the format
            return base
        answer, quote = parsed
        if is_refusal(answer):
            return base
        scores = {sid: support(quote, self.full[sid]) for sid in retrieved}
        found = sorted((s for s in retrieved if scores[s] >= THRESHOLD),
                       key=lambda s: -scores[s])
        base["quote"], base["support"] = quote, round(max(scores.values()), 2)
        if not found:                                    # quote not in the sources
            base["unsupported"] = True
            return base
        base.update(answer=f"{answer} [{', '.join(found)}]", cited=found, abstained=False)
        return base


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m src.generate "your question"')
    r = Assistant().answer(" ".join(sys.argv[1:]))
    print("Retrieved:", r["retrieved"])
    print("Answer   :", r["answer"])
    print("Quote    :", r["quote"], "| support:", r["support"])
    print("Cited    :", r["cited"], "| abstained:", r["abstained"],
          "| unsupported:", r["unsupported"])


if __name__ == "__main__":
    main()