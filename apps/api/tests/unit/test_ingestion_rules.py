"""The pure rules of the ingestion pipeline: what a question's position in the paper says about its level
(difficulty-at-upload T-01-02) and how a difficulty model's reply is read (T-02-01)."""
import pytest

from app.modules.ingestion.domain.services.difficulty_rules import BY_PART, BY_TYPE, difficulty_for

LEVELS = ("nb", "th", "vd", "vdc")  # the bank's scale, restated here: the rule may never invent a fifth level


@pytest.mark.parametrize("number,level", [(1, "nb"), (6, "nb"), (7, "th"), (10, "th"), (11, "vd"), (12, "vd")])
def test_part_one_rises_from_recall_to_application(number, level):
    assert difficulty_for("1", number, "mcq") == level


@pytest.mark.parametrize("number,level", [(1, "th"), (2, "th"), (3, "vd"), (4, "vd")])
def test_part_two_never_starts_at_recall(number, level):
    """Four statements about one setting: even the first true/false question is past nhận biết."""
    assert difficulty_for("2", number, "true_false") == level


@pytest.mark.parametrize("number,level", [(1, "vd"), (3, "vd"), (4, "vdc"), (6, "vdc")])
def test_part_three_is_the_hard_end_of_the_paper(number, level):
    assert difficulty_for("3", number, "short_answer") == level


def test_parts_are_ordered_easiest_first():
    """The convention the whole rule rests on: the same position number is harder in a later part."""
    assert [difficulty_for(p, 1, "mcq") for p in ("1", "2", "3")] == ["nb", "th", "vd"]


@pytest.mark.parametrize("number,level", [(1, "nb"), (15, "nb"), (16, "th"), (30, "th"), (31, "vd"), (37, "vd"), (38, "vdc"), (40, "vdc")])
def test_a_paper_without_parts_stretches_the_same_shape(number, level):
    """A 40-question paper has no PHẦN header; the type stands in for it and the bands stretch to its length."""
    assert difficulty_for(None, number, "mcq") == level


@pytest.mark.parametrize("qtype,number,level", [("true_false", 1, "th"), ("true_false", 4, "vd"),
                                                ("short_answer", 2, "vd"), ("short_answer", 5, "vdc"),
                                                ("essay", 1, "vd"), ("essay", 3, "vdc")])
def test_without_a_part_the_type_carries_the_convention(qtype, number, level):
    assert difficulty_for(None, number, qtype) == level


def test_a_number_past_the_last_band_keeps_the_hardest_level():
    """A paper longer than the convention expects keeps rising; it does not wrap back to nhận biết."""
    assert difficulty_for("1", 99, "mcq") == "vd"
    assert difficulty_for("3", 99, "short_answer") == "vdc"
    assert difficulty_for(None, 500, "mcq") == "vdc"


def test_an_unknown_part_or_type_still_gets_a_level():
    """Never None (ADR-02): a PHẦN IV, a missing number or a type the rule has no band table for still answers."""
    assert difficulty_for("4", 2, "true_false") == "th"       # unknown part: the type decides
    assert difficulty_for(None, None, "mcq") == "nb"          # no number: read as the first of its part
    assert difficulty_for(None, 1, "something_else") == "nb"  # unknown type: the commonest shape
    assert difficulty_for("1", None, "mcq") == "nb"


def test_every_band_names_a_level_of_the_scale():
    for bands in list(BY_PART.values()) + list(BY_TYPE.values()):
        assert [level for _, level in bands] == sorted({level for _, level in bands}, key=LEVELS.index)
        assert all(level in LEVELS for _, level in bands)
        assert [last for last, _ in bands] == sorted(last for last, _ in bands)


def test_the_rule_needs_nothing_but_its_arguments():
    """T-01-02: pure. The module reads no clock, no database and no config — its imports say so."""
    import app.modules.ingestion.domain.services.difficulty_rules as mod

    assert not [n for n in vars(mod) if not n.startswith("_") and n not in ("BY_PART", "BY_TYPE", "difficulty_for")]
