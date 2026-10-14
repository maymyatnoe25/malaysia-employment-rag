import re

import pdfplumber
from pypdf import PdfReader

PDF = "data/raw/employment_act_1955.pdf"
# merged pairs we saw in your own output
BAD = ["tobe", "hoursof", "acontract", "duringwhich", "tosick", "leavefor",
       "serviceto", "tofive", "appointmentof", "meeach", "theemployee",
       "oftheemployer", "toemployee", "isentitled", "shallbe", "tothe"]


def count(text):
    t = text.lower()
    return {w: len(re.findall(re.escape(w), t)) for w in BAD}


def main():
    a = "\n".join(p.extract_text() or "" for p in PdfReader(PDF).pages)
    with pdfplumber.open(PDF) as pdf:
        b = "\n".join(p.extract_text() or "" for p in pdf.pages)
    ca, cb = count(a), count(b)
    print(f"{'pattern':16s} {'pypdf':>6s} {'pdfplumber':>10s}")
    for w in BAD:
        print(f"{w:16s} {ca[w]:6d} {cb[w]:10d}")
    print(f"{'TOTAL':16s} {sum(ca.values()):6d} {sum(cb.values()):10d}")
    print("characters:", len(a), len(b))


if __name__ == "__main__":
    main()