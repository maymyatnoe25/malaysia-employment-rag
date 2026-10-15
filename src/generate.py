import re
import sys

import requests

from src.retrieve import Retriever
from src.search import load_sections, make_units

OLLAMA = "http://localhost:11434/api/generate"
LLM = "llama3.2"

PROMPT = """You answer questions about the Malaysian Employment Act 1955 for employees.
Use ONLY the sources below.

Reply in exactly this format:
ANSWER: <1 to 3 plain sentences>
QUOTE: <one sentence copied word for word from the sources that supports your answer>

If the sources do not contain the answer, reply with exactly: NOT_FOUND
Do not guess. Do not use outside knowledge.

Sources:
{sources}

Question: {question}
"""


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


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
    """Return (answer, quote) or None when the model refused or broke the format."""
    m = re.search(r"ANSWER:\s*(.*?)\s*QUOTE:\s*(.*)", raw, re.S | re.I)
    if m:
        quote = re.sub(r"\[[^\]]*\]", "", m.group(2)).strip(" \"'\u201c\u201d\n")
        return m.group(1).strip(), quote
    return None


def refused(raw):
    return bool(re.search(r"NOT[\s_-]*FOUND", raw, re.I)) and parse(raw) is None


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
                "answer": "NOT_FOUND"}
        if refused(raw):
            return base
        parsed = parse(raw)
        if parsed is None:                       # wrong format: do not trust it
            base["unsupported"] = True
            return base
        answer, quote = parsed
        q = norm(quote)
        found = [sid for sid in retrieved if len(q) >= 30 and q in norm(self.full[sid])]
        if not found:                            # quote is not in the sources
            base["unsupported"], base["quote"] = True, quote
            return base
        base.update(answer=f"{answer} [{', '.join(found)}]", quote=quote,
                    cited=found, abstained=False)
        return base


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m src.generate "your question"')
    r = Assistant().answer(" ".join(sys.argv[1:]))
    print("Retrieved:", r["retrieved"])
    print("Answer   :", r["answer"])
    print("Quote    :", r["quote"])
    print("Cited    :", r["cited"], "| abstained:", r["abstained"],
          "| unsupported:", r["unsupported"])


if __name__ == "__main__":
    main()