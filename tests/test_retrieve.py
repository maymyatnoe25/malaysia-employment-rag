import numpy as np

from src.retrieve import rank_positions, top_sections


def test_rank_positions():
    assert list(rank_positions(np.array([0.1, 0.9, 0.5]))) == [3, 1, 2]


def test_top_sections_one_per_section():
    units = [{"section_id": "a"}, {"section_id": "a"}, {"section_id": "b"}]
    out = top_sections(units, np.array([0.9, 0.8, 0.7]), k=2)
    assert [u["section_id"] for u, _ in out] == ["a", "b"]