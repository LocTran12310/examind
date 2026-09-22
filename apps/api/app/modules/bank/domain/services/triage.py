"""Triage of freshly parsed questions (US-01, A-02, A-03, A-07): near-duplicates, auto-approve vs review, spot checks."""
import random
import re

from app.modules.bank.domain.entities import Question

DUPLICATE_SIMILARITY = 0.9
SPOT_RATIO = 0.05
MIN_DUPLICATE_TEXT = 15


def is_duplicate(q: Question, other_text: str, similarity: float) -> bool:
    """Near-identical text is a duplicate unless the numbers differ (same wording, other numbers = another question)."""
    return similarity >= DUPLICATE_SIMILARITY and re.findall(r"\d+", other_text) == re.findall(r"\d+", q.search_text)


def spot_sample(auto: list[Question], seed: str) -> list[Question]:
    """About 5% of the auto-approved questions (at least one), drawn reproducibly."""
    if not auto:
        return []
    return random.Random(seed).sample(auto, max(1, round(len(auto) * SPOT_RATIO)))
