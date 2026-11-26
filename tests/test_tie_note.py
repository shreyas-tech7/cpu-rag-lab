"""The tie sentence under a top table shows only when the intervals overlap."""

from cpu_rag_lab.report import tie_note


def row(lo: float, hi: float) -> dict:
    return {"metrics": {"ndcg@10": {"mean": (lo + hi) / 2, "lo": lo, "hi": hi}}}


def test_note_when_all_five_overlap_the_best():
    top = [row(0.70, 0.80), row(0.69, 0.79), row(0.68, 0.78), row(0.66, 0.76), row(0.65, 0.71)]
    assert tie_note(top) == "The intervals of these five rows overlap, so treat them as a tie."


def test_no_note_when_one_row_falls_below_the_best_interval():
    """Broken case: the last row's interval ends below the best row's lower bound."""
    top = [row(0.70, 0.80), row(0.69, 0.79), row(0.68, 0.78), row(0.66, 0.76), row(0.60, 0.69)]
    assert tie_note(top) == ""


def test_no_note_for_a_single_row():
    assert tie_note([row(0.70, 0.80)]) == ""
