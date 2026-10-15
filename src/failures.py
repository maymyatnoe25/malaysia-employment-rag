from src.evaluate import first_gold_rank, load_questions
from src.retrieve import Retriever
from src.search import load_sections, make_units


def main():
    retriever = Retriever(make_units(load_sections(), max_chars=1200), "minilm")
    for q in load_questions():
        if q["kind"] != "answer" or q["split"] != "test":
            continue
        hits = retriever.search(q["question"], "hybrid", k=5)
        ids = [u["section_id"] for u, _ in hits]
        rank = first_gold_rank(ids, q["gold"])
        if rank is None or rank > 1:
            print(f"{q['id']} rank={rank} gold={q['gold']} got={ids[:3]}")
            print("    ", q["question"][:90])


if __name__ == "__main__":
    main()