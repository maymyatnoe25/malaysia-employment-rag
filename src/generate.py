import re
import sys

import requests

from src.retrieve import Retriever
from src.search import load_sections, make_units

OLLAMA = "http://localhost:11434/api/generate"
LLM = "llama3.2"

PROMPT = """You answer questions about the Malaysian Employment Act 1955 for employees.
Use ONLY the numbered sources below.

Rules:
1. Answer in 1 to 4 plain sentences.
2. After each claim, cite the section in square brackets, like [s60F].
3. Only cite sections that appear in the sources below.
4. Reply with exactly NOT_FOUND only if none of the sources contains information that answers the question.
5. Do not use outside knowledge. Do not guess numbers.

Sources:
{sources}

Question: {question}
Answer:"""


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


def cited_ids(answer):
    """Section ids cited like [s60F] or [s60F, s37]."""
    ids = []
    for group in re.findall(r"\[([^\]]+)\]", answer):
        for part in group.split(","):
            m = re.fullmatch(r"\s*s(\d+[A-Za-z]{0,2})\s*", part)
            if m:
                ids.append("s" + m.group(1).upper())
    return ids


def abstained(answer):
    return "NOT_FOUND" in answer.upper().replace(" ", "_")


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
        text = ask_llm(prompt, self.model)
        return {"question": question, "answer": text,
                "retrieved": [u["section_id"] for u, _ in hits],
                "cited": cited_ids(text), "abstained": abstained(text)}


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m src.generate "your question"')
    r = Assistant().answer(" ".join(sys.argv[1:]))
    print("Retrieved:", r["retrieved"])
    print("Answer   :", r["answer"])
    print("Cited    :", r["cited"], "| abstained:", r["abstained"])


if __name__ == "__main__":
    main()