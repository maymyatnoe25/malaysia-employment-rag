from src.chunk import clean_lines, split_sections


def run(text):
    lines = clean_lines([{"page": 1, "text": text}])
    return split_sections(lines)


def test_headers_removed_and_sections_split():
    text = "\n".join([
        "Laws of Malaysia", "2", "Act 265", "EMPLOYMENT ACT 1955",
        "An Act relating to employment.",
        "PART I", "PRELIMINARY",
        "Short title",
        "1. This Act may be cited as the Employment Act 1955.",
        "Appeals",
        "4. Any person may appeal.",
        "(1) In writing.",
    ])
    lines = clean_lines([{"page": 1, "text": text}])
    assert all("Laws of Malaysia" not in line for _, line in lines)

    chunks, _ = split_sections(lines)
    assert [c["section"] for c in chunks] == ["1", "4"]
    assert chunks[0]["heading"] == "Short title"
    assert chunks[1]["heading"] == "Appeals"
    assert chunks[1]["part"] == "PART I PRELIMINARY"


def test_lowercase_lettered_sections():
    text = "\n".join([
        "An Act relating to employment.",
        "Work on rest day",
        "1. (1) Except as provided, no employee shall work.",
        "Hours of work",
        "1a. (1) An employee shall not be required to work.",
        "Paternity leave",
        "1fa. (1) A married male employee shall be entitled.",
    ])
    chunks, _ = run(text)
    assert [c["id"] for c in chunks] == ["s1", "s1A", "s1FA"]
    assert chunks[1]["heading"] == "Hours of work"
    assert chunks[2]["heading"] == "Paternity leave"


def test_amendment_table_is_cut_off():
    text = "\n".join([
        "An Act relating to employment.",
        "Short title",
        "1. This Act may be cited as the Employment Act 1955.",
        "60fa Act A1651 01-01-2023",
        "60g Act A91",
    ])
    chunks, _ = run(text)
    assert [c["id"] for c in chunks] == ["s1"]
    assert "Act A1651" not in chunks[0]["text"]