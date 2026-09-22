"""The canonical line stream every extractor produces (ADR-02).

`text` is Markdown: math as `$…$`, images as `![](asset:<id>)`. Extractors keep emphasis that can
mark a correct option (`**…**`, `[…]{.underline}`, `[…]{.mark}`) so the splitter can read it.
"""
from dataclasses import dataclass, field
import re

from app.shared.domain.text import strip_markup  # noqa: F401  (the extractors and the splitter import it from here)


@dataclass
class Line:
    text: str
    page: int | None = None
    ocr: bool = False
    confidence: float | None = None  # OCR confidence 0–1 when ocr=True
    meta: dict = field(default_factory=dict)




def is_emphasised_label(fragment: str) -> bool:
    """True when an option label itself carries emphasis, e.g. `**C.**`, `[C.]{.underline}`."""
    f = fragment.strip()
    return bool(re.match(r"^(\*\*|__)?\[[A-Da-d]\]\{\.(underline|mark)\}[.)]", f)  # "**[B]{.underline}.**"
                or re.match(r"^(\*\*|__)[A-Da-d][.)]?(\*\*|__)", f) or re.match(r"^\[[A-Da-d][.)]?\]\{\.(underline|mark)\}", f)
                or re.match(r"^\*\*\[[A-Da-d][.)]?\]\{\.(underline|mark)\}\*\*", f))
