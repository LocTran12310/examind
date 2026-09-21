import pytest

from app.services.scoring import grade, same_short_answer, scaled


def test_mcq():
    assert grade("mcq", {"key": "B"}, {"key": "B"}, 0.25).points == 0.25
    g = grade("mcq", {"key": "B"}, {"key": "C"}, 0.25)
    assert g.points == 0 and g.is_correct is False
    assert grade("mcq", {"key": "B"}, None, 0.25).points == 0


@pytest.mark.parametrize("right,share", [(0, 0), (1, 0.1), (2, 0.25), (3, 0.5), (4, 1.0)])
def test_true_false_partial_credit(right, share):
    key = {"a": True, "b": False, "c": True, "d": True}
    labels = list(key)
    response = {k: (key[k] if i < right else not key[k]) for i, k in enumerate(labels)}
    g = grade("true_false", key, response, 1.0)
    assert g.points == pytest.approx(share) and g.is_correct is (right == 4)


def test_true_false_unanswered_statements_count_wrong():
    assert grade("true_false", {"a": True, "b": False, "c": True, "d": True}, {"a": True}, 1.0).points == pytest.approx(0.1)


@pytest.mark.parametrize("key,given,ok", [
    ("2,5", "2.5", True), ("2,5", "5/2", True), ("-3", "−3", True), ("0.5", "1/2", True),
    ("1", "1,0", True), ("2", "3", False), ("Hà Nội", "ha noi", True), ("x", "", False), ("1/0", "1", False),
])
def test_short_answer_normalisation(key, given, ok):
    assert same_short_answer(key, given) is ok


def test_essay_needs_teacher_and_scaling():
    g = grade("essay", {"text": "..."}, {"text": "bài làm"}, 2.0)
    assert g.points is None and g.max_points == 2.0
    assert scaled(7.25, 10) == 7.25 and scaled(3, 4) == 7.5 and scaled(0, 0) == 0
