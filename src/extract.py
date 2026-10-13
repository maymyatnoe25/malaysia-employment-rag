import json
from pathlib import Path

from pypdf import PdfReader

RAW = Path("data/raw")
OUT = Path("data/processed")


def extract(pdf_path):
    reader = PdfReader(pdf_path)
    return [{"page": i, "text": page.extract_text() or ""}
            for i, page in enumerate(reader.pages, start=1)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(RAW.glob("*.pdf")):
        pages = extract(pdf)
        (OUT / f"{pdf.stem}.json").write_text(
            json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
        chars = sum(len(p["text"]) for p in pages)
        empty = sum(1 for p in pages if len(p["text"].strip()) < 50)
        print(f"{pdf.name}: {len(pages)} pages, {chars} characters, "
              f"{empty} near-empty pages")


if __name__ == "__main__":
    main()