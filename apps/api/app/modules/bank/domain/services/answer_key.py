"""Parse a pasted answer key (A-06): '1A 2C 3B', '1.A, 2.C', '1-A', 'PHẦN I: 1A 2B', or one letter per line."""
import re

from app.shared.domain.text import PART_RE, ROMAN

PAIR = re.compile(r"(?<!\d)(\d{1,3})\s*[.\-:)]?\s*([A-Da-d])(?![A-Za-zÀ-ỹ])")


def parse(text: str) -> dict[tuple[str | None, int], str]:
    out: dict[tuple[str | None, int], str] = {}
    part: str | None = None
    lone: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        pm = PART_RE.match(line)
        if pm:
            token = pm.group(1).upper()
            part = str(ROMAN.get(token, token))
            line = pm.group(2)
        pairs = PAIR.findall(line)
        if pairs:
            for n, letter in pairs:
                out[(part, int(n))] = letter.upper()
        elif re.fullmatch(r"[A-Da-d]", line):
            lone.append(line.upper())
    if lone and not out:
        out = {(None, i): letter for i, letter in enumerate(lone, start=1)}
    return out
