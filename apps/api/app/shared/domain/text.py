"""Text conventions of Vietnamese exam papers shared by ingestion and the bank: the emphasis markup the
extractors inject and the `PHẦN I/II/III` part headers."""
import re

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
PART_RE = re.compile(r"^(?:PHẦN|Phần)\s+(I{1,3}|IV|V|[1-5])\b\s*[.:]?\s*(.*)$", re.U)

_MARKUP = re.compile(r"\*\*|__|\{\.(?:underline|mark)\}|(?<!\!)\[(?=[^\]]*\]\{\.(?:underline|mark)\})|\](?=\{\.(?:underline|mark)\})")


def strip_markup(text: str) -> str:
    """Remove the emphasis markup we inject, keeping content (used for matching only)."""
    return _MARKUP.sub("", text)
