import re
import sys

from src.search import load_sections


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m src.context "word" [width]')
    word = sys.argv[1]
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    pat = re.compile(r".{0,%d}%s.{0,%d}" % (width, re.escape(word), width),
                     re.I | re.S)
    for s in load_sections():
        for n, m in enumerate(pat.finditer(s["body"])):
            if n == 2:
                break
            print(f"[{s['id']}] ...{m.group().replace(chr(10), ' ')}...")


if __name__ == "__main__":
    main()