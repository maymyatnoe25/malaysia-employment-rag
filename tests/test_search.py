from src.search import BM25Index, make_units, tokenize


def fake_sections():
    return [
        {"id": "s1", "section": "1", "heading": "Rest day", "part": "P",
         "page_start": 1, "page_end": 1,
         "body": "Every employee shall be allowed one rest day in each week."},
        {"id": "s2", "section": "2", "heading": "Annual leave", "part": "P",
         "page_start": 2, "page_end": 2,
         "body": "An employee shall be entitled to paid annual leave of eight days."},
        {"id": "s3", "section": "3", "heading": "Definitions", "part": "P",
         "page_start": 3, "page_end": 3,
         "body": "; ".join(f"item number {i} means something" for i in range(200))},
    ]


def test_tokenize_drops_stopwords():
    assert tokenize("What is the Rest Day?") == ["rest", "day"]


def test_long_sections_are_split_and_keep_their_heading():
    units = make_units(fake_sections(), max_chars=300)
    long_units = [u for u in units if u["section_id"] == "s3"]
    assert len(long_units) > 1
    assert all(len(u["text"]) < 400 for u in long_units)
    assert all(u["text"].startswith("Section 3. Definitions") for u in long_units)


def test_search_finds_the_right_section():
    index = BM25Index(make_units(fake_sections(), max_chars=300))
    top = index.search("how much annual leave do I get", k=1)[0][0]
    assert top["section_id"] == "s2"