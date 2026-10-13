from src.evaluate import first_gold_rank, summarize


def test_first_gold_rank():
    assert first_gold_rank(["a", "b", "c"], ["c", "b"]) == 2
    assert first_gold_rank(["a", "b"], ["z"]) is None


def test_summarize():
    s = summarize([1, 2, None, 4])
    assert s["hit@1"] == 0.25
    assert s["hit@3"] == 0.5
    assert abs(s["mrr"] - (1 + 0.5 + 0 + 0.25) / 4) < 1e-9