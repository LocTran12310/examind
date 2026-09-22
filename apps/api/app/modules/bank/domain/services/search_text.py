"""Normalised text used for search, near-duplicate detection and kNN (question-review ADR-01)."""
import re

from unidecode import unidecode

_ASSET = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MARKUP = re.compile(r"\*\*|__|\{\.(?:underline|mark)\}|[\[\]]")
_LATEX_CMD = re.compile(r"\\[A-Za-z]+")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalise(text: str) -> str:
    """Letters and digits only, unaccented: Word's `$x^{2}$` and a PDF's `x²` both become `x2`."""
    t = _ASSET.sub(" ", text or "")
    t = _MARKUP.sub(" ", t)
    t = _LATEX_CMD.sub(" ", t)
    t = unidecode(t).lower()
    return _NON_ALNUM.sub("", t)


def query(text: str) -> str:
    return normalise(text)


def for_question(stem: str, options: list[dict] | None) -> str:
    parts = [stem or ""] + [o.get("content", "") for o in options or []]
    return normalise(" ".join(parts))[:4000]
