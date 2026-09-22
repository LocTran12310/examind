"""How two short answers compare (exam-practice A-03). Shared by grading (assessment) and answer-key checks (ingestion)."""
from fractions import Fraction
import re

from unidecode import unidecode


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
