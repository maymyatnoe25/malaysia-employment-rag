from src.evaluate import load_questions
from src.search import load_sections, tokenize


def main():
    sections = {s["id"]: s for s in load_sections()}
    for q in load_questions():
        if q["kind"] != "answer":
            continue
        words = set(tokenize(q["question"]))
        gold_words = set()
        for g in q["gold"]:
            gold_words |= set(tokenize(sections[g]["text"]))
        share = len(words & gold_words) / max(len(words), 1)
        flag = "  <- uses the Act's own words" if share > 0.8 else ""
        print(f"{q['id']} {q['split']:4s} overlap {share:.2f}{flag}")


if __name__ == "__main__":
    main()