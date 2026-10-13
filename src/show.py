import sys

from src.search import load_sections


def norm(x):
    x = x.strip()
    if x[:1].lower() == "s" and x[1:2].isdigit():
        x = x[1:]
    return "s" + x.upper()


def main():
    sections = load_sections()
    if len(sys.argv) >= 3 and sys.argv[1] == "--grep":
        word = " ".join(sys.argv[2:]).lower()
        hits = [s["id"] for s in sections if word in s["text"].lower()]
        print(f"'{word}' appears in {len(hits)} sections:", hits)
        return
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m src.show s60F   |   python -m src.show --grep word")
    want = norm(sys.argv[1])
    for s in sections:
        if s["id"] == want:
            print(s["id"], "|", s["heading"], "|", s["part"], "| pages",
                  s["page_start"], "-", s["page_end"])
            print(s["body"])
            return
    print("No such section id:", want)


if __name__ == "__main__":
    main()