import json
import re
import statistics
from pathlib import Path

SRC = Path("data/processed/employment_act_1955.json")
OUT = Path("data/processed/chunks.jsonl")

# Lines that repeat on every page (headers, footers, page numbers).
NOISE_RE = [re.compile(p, re.I) for p in (
    r"^Laws of Malaysia$",
    r"^Act 265$",
    r"^EMPLOYMENT ACT 1955$",
    r"^Employment$",
    r"^\d{1,3}$",
    r"^WJW23/.*$",
)]
# "60a. (1) ..." / "60 e. ..." / "60. (1) ..."  (letters can be lowercase)
SECTION_RE = re.compile(r"^(\d{1,3})\s?([A-Za-z]{0,2})\s?\.\s+(\S.*)$")
PART_RE = re.compile(r"^PART\s+[IVXLC]+[A-Z]?$", re.I)
SCHEDULE_RE = re.compile(
    r"^(first|second|third|fourth|fifth|sixth|seventh)\s+schedule$", re.I)
# The table of amendments at the end: "60fa Act A1651 01-01-2023"
END_RE = re.compile(r"^\d{1,3}\s?[A-Za-z]{0,2}\s+(Act\s+A?\d+|P\.?\s?U\.|Ord\.)", re.I)
PARA_RE = re.compile(r"^\(\w{1,4}\)")                          # e.g. "(1)", "(a)"
REMOVED_RE = re.compile(r"\(\s*(omitted|deleted)", re.I)
BODY_START = "An Act relating to employment."
MAX_GAP = 20          # real sections go up in order, with small jumps


def clean_lines(pages):
    """Return (page, line) pairs without blank or repeated header/footer lines.
    Stops at the table of amendments and at the printer's footer."""
    out = []
    for p in pages:
        for raw in p["text"].splitlines():
            line = raw.strip()
            if line.upper().startswith("DICETAK OLEH") or END_RE.match(line):
                return out
            if not line or any(rx.match(line) for rx in NOISE_RE):
                continue
            out.append((p["page"], line))
    return out


def is_heading(line):
    """Headings are short and do not end like a sentence."""
    return (len(line) <= 90 and not line.startswith("(")
            and not re.search(r"[.;:,)\u2014-]$", line)
            and not re.search(r"P\s?\.\s?U\.|\]|\*|Act A\d", line))


def pop_heading(buf):
    """Remove up to 3 heading-like lines from the end of buf and return them."""
    heading = []
    while buf and len(heading) < 3 and is_heading(buf[-1]):
        heading.insert(0, buf.pop())
    return heading


def to_paragraphs(lines):
    """Join wrapped lines; start a new paragraph at (1), (a), ..."""
    paras = []
    for line in lines:
        if not paras or PARA_RE.match(line):
            paras.append(line)
        else:
            paras[-1] += " " + line
    return "\n".join(paras)


def split_sections(lines):
    start = next((i for i, (_, l) in enumerate(lines) if l == BODY_START), None)
    if start is None:
        raise ValueError("Could not find the start of the Act body")
    lines = lines[start + 1:]          # skips the table of contents

    chunks, cur, buf = [], None, []
    part, last_num, in_schedule, skipped = "", 0, False, []
    prev_page = lines[0][0] if lines else 1

    def close(last_page):
        if cur is None:
            return
        body = to_paragraphs(buf)
        if REMOVED_RE.search(body) and len(body) < 60:
            return                                  # "(Omitted)" / "(Deleted)"
        cur["page_end"] = last_page
        cur["body"] = body
        if cur["heading"]:
            cur["text"] = f"Section {cur['section']}. {cur['heading']}\n{body}"
        else:
            cur["text"] = f"{cur['section']}\n{body}"
        chunks.append(cur)

    i = 0
    while i < len(lines):
        page, line = lines[i]
        i += 1

        if not in_schedule and PART_RE.match(line):
            part = line.upper()
            if i < len(lines) and lines[i][1].isupper():
                part += " " + lines[i][1]
                i += 1
            continue

        if SCHEDULE_RE.match(line):
            close(prev_page)
            in_schedule = True
            name = " ".join(line.split()).title()
            cur = {"id": name.lower().replace(" ", "_"), "section": name,
                   "heading": "", "part": part, "page_start": page}
            buf = []
            prev_page = page
            continue

        m = None if in_schedule else SECTION_RE.match(line)
        if m:
            num = int(m.group(1))
            if last_num <= num <= last_num + MAX_GAP:
                sec = m.group(1) + m.group(2).upper()      # "60a" -> "60A"
                heading = pop_heading(buf)
                close(prev_page)
                cur = {"id": "s" + sec, "section": sec,
                       "heading": " ".join(heading), "part": part,
                       "page_start": page}
                buf = [m.group(3)]
                last_num = num
                prev_page = page
                continue
            skipped.append(line[:70])                # looked like a section but wasn't

        buf.append(line)
        prev_page = page

    close(prev_page)
    return chunks, skipped


def main():
    pages = json.loads(SRC.read_text(encoding="utf-8"))
    chunks, skipped = split_sections(clean_lines(pages))

    with OUT.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    lengths = [len(c["text"]) for c in chunks]
    ids = {c["id"] for c in chunks}
    print("Chunks:", len(chunks))
    print("Characters per chunk: min", min(lengths),
          "| median", int(statistics.median(lengths)), "| max", max(lengths))
    print("Chunks without a heading:",
          [c["id"] for c in chunks if not c["heading"]])
    print("Longest chunks:", [(c["id"], len(c["text"])) for c in
                              sorted(chunks, key=lambda c: -len(c["text"]))[:6]])
    print("Lines ignored as 'not a section':", len(skipped), skipped[:6])
    wanted = ["s12", "s14", "s37", "s60", "s60A", "s60D", "s60E", "s60F",
              "s60FA", "s60P", "s60Q"]
    print("Expected sections present:", {w: (w in ids) for w in wanted})
    print("Last 6 chunk ids:", [c["id"] for c in chunks[-6:]])

    for want in ("s1", "s60A", "s60FA"):
        for c in chunks:
            if c["id"] == want:
                print(f"\n--- {want} ---")
                print(c["heading"], "|", c["part"], "| pages",
                      c["page_start"], "-", c["page_end"])
                print(c["text"][:350].replace("\n", " / "))


if __name__ == "__main__":
    main()