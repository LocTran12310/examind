"""Pure grading rules (exam-practice ADR-04, A-02, A-03)."""
from dataclasses import dataclass
from fractions import Fraction
import re

from unidecode import unidecode

# THPT 2025 true/false partial credit: number of correct statements → share of the question's points.
TF_PARTIAL = {0: 0.0, 1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}


@dataclass(frozen=True)
class Grade:
    points: float | None      # None = needs a teacher (essay)
    max_points: float
    is_correct: bool | None
    ratio: float | None


def _num(s: str) -> Fraction | None:
    t = (s or "").strip().replace(" ", "").replace("−", "-").replace(",", ".")
    t = t.strip("$")
    try:
        if re.fullmatch(r"-?\d+(\.\d+)?/-?\d+(\.\d+)?", t):
            a, b = t.split("/")
            return Fraction(a) / Fraction(b)
        if re.fullmatch(r"-?\d+(\.\d+)?", t):
            return Fraction(t)
    except (ValueError, ZeroDivisionError):
        return None
    return None


def same_short_answer(key: str, given: str) -> bool:
    a, b = _num(key), _num(given)
    if a is not None and b is not None:
        return abs(a - b) <= Fraction(1, 10**9)
    norm = lambda s: re.sub(r"\s+", " ", unidecode(s or "").strip().lower())  # noqa: E731
    return bool(norm(given)) and norm(key) == norm(given)


def grade(qtype: str, key: dict | None, response: dict | None, points: float) -> Grade:
    response = response or {}
    if qtype == "essay":
        return Grade(None, points, None, None)
    if not key:
        return Grade(0.0, points, False, 0.0)
    if qtype == "mcq":
        ok = bool(response.get("key")) and response.get("key") == key.get("key")
        return Grade(points if ok else 0.0, points, ok, 1.0 if ok else 0.0)
    if qtype == "true_false":
        labels = [k for k, v in key.items() if isinstance(v, bool)]
        correct = sum(1 for k in labels if response.get(k) is key[k])
        if len(labels) == 4:
            share = TF_PARTIAL[correct]
        else:
            share = correct / len(labels) if labels else 0.0
        return Grade(round(points * share, 4), points, correct == len(labels) and bool(labels), share)
    if qtype == "short_answer":
        ok = same_short_answer(str(key.get("value", "")), str(response.get("value", "")))
        return Grade(points if ok else 0.0, points, ok, 1.0 if ok else 0.0)
    return Grade(0.0, points, False, 0.0)


def scaled(score: float, max_score: float, scale_to: float = 10) -> float:
    if not max_score:
        return 0.0
    return round(score / max_score * scale_to, 2)
