import sys

from src.evaluate import load_questions
from src.search import load_sections


def main():
    only = set(sys.argv[1:])
    sections = {s["id"]: s for s in load_sections()}
    for q in load_questions():
        if only and q["id"] not in only:
            continue
        print("=" * 70)
        print(q["id"], q["split"], q["kind"], "|", q["question"])
        for g in q["gold"]:
            s = sections.get(g)
            if not s:
                print("  !! no such section:", g)
                continue
            print(f"  [{g}] {s['heading']}")
            print("   ", s["body"][:450].replace("\n", " "))


if __name__ == "__main__":
    main()