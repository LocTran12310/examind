"""Rule-based exam splitter (exam-ingestion ADR-02, A-01..A-04).

Pure function over the line stream: no I/O, deterministic, table-tested. Recognises
- question headers `Câu N` / `Bài N` (and bare `N.` when a document has no `Câu` headers),
- THPT-2025 parts (`PHẦN I/II/III`) and their question types,
- options `A.`–`D.` on one or many lines, true/false statements `a)`–`d)`,
- answers inline (`Đáp án: C`, `Chọn C`), in an answer key (list or table), or by emphasis on the option label,
- solutions right after a question or in a trailing section that restarts numbering.
"""
from dataclasses import dataclass, field
import re

from app.modules.ingestion.domain.services.lines import Line, is_emphasised_label, strip_markup
from app.shared.domain.answers import same_short_answer
from app.shared.domain.question_quality import evaluate
from app.shared.domain.text import PART_RE, ROMAN  # noqa: F401  (answer keys read the same part headers)

AUTO_APPROVE_DEFAULT = 0.85

_HDR_WORDS = r"(?:Câu|CÂU|Bài|BÀI|Question|QUESTION)"
QUESTION_RE = re.compile(rf"^{_HDR_WORDS}\s*(\d{{1,3}})\s*(?:\(([^)]*)\))?\s*[.:)]?\s*", re.U)
# Same header, tolerant of our emphasis markup around it, used to cut it off the raw text.
QUESTION_RAW_RE = re.compile(rf"^(?:\*\*|__)?\s*{_HDR_WORDS}\s*\d{{1,3}}\s*(?:\([^)]*\))?\s*[.:)]?\s*(?:\*\*|__)?\s*[.:]?\s*", re.U)
NUMBERED_RE = re.compile(r"^(\d{1,3})\s*[.)]\s+(?=\S)")
KEY_HEADER_RE = re.compile(r"^(?:BẢNG\s+ĐÁP\s+ÁN|ĐÁP\s+ÁN(?:\s+THAM\s+KHẢO)?|Bảng\s+đáp\s+án|Đáp\s+án\s+tham\s+khảo)\s*[.:]?\s*$", re.U)
# Upper-case only: "Lời giải" in mixed case starts a per-question solution, not a section.
SOLUTION_SECTION_RE = re.compile(
    r"^(?:HƯỚNG\s+DẪN\s+GIẢI|LỜI\s+GIẢI|ĐÁP\s+ÁN\s+VÀ\s+(?:HƯỚNG\s+DẪN\s+GIẢI|LỜI\s+GIẢI))(?:\s+CHI\s+TIẾT)?\s*[.:]?\s*$", re.U)
SOLUTION_START_RE = re.compile(r"^(?:Lời\s+giải|Hướng\s+dẫn\s+giải|Hướng\s+dẫn|Giải|LỜI\s+GIẢI)(?:\s+chi\s+tiết)?\s*(?:[.:]\s*|$)", re.U | re.I)
# Sub-headings of official solutions: they start the solution and are kept as bold headings (A-04).
SOLUTION_HEAD_RE = re.compile(r"^(Phương\s+pháp(?:\s+giải)?|Cách\s+giải)\s*[.:]\s*", re.U | re.I)
INLINE_ANSWER_RE = re.compile(r"^(?:Đáp\s+án|Chọn|ĐÁP\s+ÁN|CHỌN)(?:\s+đúng)?\s*[:.]?\s*(?:đáp\s+án\s+)?([A-D])(?=[\s.,;]|$)", re.U)
CHOOSE_IN_TEXT_RE = re.compile(r"(?:Chọn|chọn|CHỌN)\s+(?:đáp\s+án\s+|phương\s+án\s+)?([A-D])(?=[\s.,;)]|$)", re.U)
SHORT_ANSWER_RE = re.compile(r"^(?:Đáp\s+án|Đáp\s+số|Trả\s+lời|Kết\s+quả|ĐÁP\s+ÁN|ĐÁP\s+SỐ)\s*[:.]\s*(.+)$", re.U)
TF_STATEMENT_RE = re.compile(r"^(?:\*\*)?([a-d])\s*[).]\s*(?:\*\*)?\s*(.*)$", re.U)
TF_VERDICT_RE = re.compile(r"(?<![A-Za-zÀ-ỹ])([a-d])[ \t]*[).]?[ \t]*[:\-–]?[ \t]*(Đúng|Sai|ĐÚNG|SAI|đúng|sai|Đ|S|Ð)(?![A-Za-zÀ-ỹ])", re.U)
# An option marker: optional emphasis, a capital A–D, "." or ")", optional emphasis, then space/end.
OPTION_RE = re.compile(
    r"(?:(?<=^)|(?<=\s)|(?<=\|)|(?<=\s\[)|(?<=^\[))"
    # the label alone may be underlined: "**[B]{.underline}.**"
    r"(?P<mark>(?:\*\*)?(?:\[)?(?P<label>[A-D])(?:\]\{\.(?:underline|mark)\})?(?P<delim>[.)])(?:\]\{\.(?:underline|mark)\})?(?:\*\*)?)"
    # a space normally follows the label; OCR often drops it ("D.14", "B.(2;1)")
    r"(?=\s|$|(?<=[.)])(?=[^\s.,;:]))", re.U)

# Cyrillic look-alikes typed as option labels ("А." with U+0410) — labels only (AC-07)
LOOKALIKE_LABEL_RE = re.compile(r"(?:(?<=^)|(?<=[\s*\[|]))([АВС])(?=(?:\]\{\.(?:underline|mark)\})?[.)])", re.U)
LOOKALIKES = {"А": "A", "В": "B", "С": "C"}
# A row of an answer table: "Câu | 1 | 2 …", "Mã đề | Câu 1 | …", "Đáp án | 3 | 20 …", "| C | A | …"
KEY_ROW_HEAD_RE = re.compile(r"^(?:câu|mã\s+đề|đề)$", re.I | re.U)
KEY_LABEL_RE = re.compile(r"^(?:câu|mã\s+đề|đề|đáp\s+án|đa|trả\s+lời|kết\s+quả|chọn)$", re.I | re.U)
EMPTY_ANSWER_RE = re.compile(r"^(?:Đáp\s+án|ĐÁP\s+ÁN)\s*:?\s*$", re.U)
# The end of an exam ("🙢 HẾT 🙠", "---HẾT---") and the header block official files repeat before their
# answer key / solutions: they close the question being read, they are never part of it.
END_RE = re.compile(r"^[\s\-–—_=*.🙢🙠•]*(?:HẾT|Hết)[\s\-–—_=*.!🙢🙠•]*$", re.U)
DOC_HEADER_RE = re.compile(
    r"^(?:SỞ\s|BỘ\s+GIÁO\s+DỤC|TRƯỜNG\s|KHỐI\s+THPT|K[ÌỲ]\s+THI\b|ĐỀ\s+(?:THI|KIỂM\s+TRA|KHẢO\s+SÁT|CHÍNH\s+THỨC|ONLINE|ÔN)|"
    r"NĂM\s+HỌC\b|MÔN(?:\s+THI)?\s*:|Môn\s*:|Bài\s+thi\s*:|\(?\s*Thời\s+gian(?:\s+làm\s+bài)?\s*:?\s*\d+\s*phút|Mã\s+đề|"
    r"Họ(?:\s+và)?\s+tên(?:\s+thí\s+sinh)?\s*:|SBD\s*:|Số\s+báo\s+danh|Đề\s+gồm\s+có|Ngày\s+thi\b|\(\s*Thí\s+sinh\s+không|\(\s*Đề\s+thi\s+có)", re.U)
KEY_ROW_RE = re.compile(r"^(?:\s*\|?\s*\d{1,3}\s*[.:\-)]\s*[A-D]\s*\|?)+\s*$", re.U)


def _boundary(plain: str) -> bool:
    return len(plain) <= 160 and bool(END_RE.match(plain) or DOC_HEADER_RE.match(plain))


def _key_row(plain: str) -> bool:
    """"1.B | 2.C | 3.A …" (a row of a Phần I key), at least three pairs."""
    return bool(KEY_ROW_RE.match(plain)) and len(re.findall(r"\d{1,3}\s*[.:\-)]\s*[A-D]", plain)) >= 3


THPT_PART_TYPES = {"1": "mcq", "2": "true_false", "3": "short_answer"}

CHOICE_WORDS_RE = re.compile(r"(?:lựa\s+chọn|phương\s+án|đáp\s+án)", re.I | re.U)

PART_TYPE_WORDS = [
    ("true_false", ("đúng sai", "đúng/sai", "đúng - sai", "đúng – sai")),
    ("short_answer", ("trả lời ngắn",)),
    ("essay", ("tự luận",)),
    ("mcq", ("nhiều phương án", "trắc nghiệm")),
]


@dataclass
class ParsedQuestion:
    number: int
    part: str | None = None
    type: str = "mcq"
    stem: str = ""
    options: list[dict] = field(default_factory=list)
    answer: dict | None = None
    answer_source: str | None = None
    solution: str = ""
    confidence: float = 1.0
    issues: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)
    raw: str = ""
    ocr: bool = False
    marked_labels: list[str] = field(default_factory=list)


@dataclass
class _Block:
    part: str | None
    number: int
    lines: list[Line]
    kind: str = "question"  # question | solution


@dataclass
class SplitResult:
    questions: list[ParsedQuestion]
    preamble: list[str]
    warnings: list[str]


def _part_label(token: str) -> str:
    token = token.upper()
    return str(ROMAN.get(token, token))


def _part_type(header_rest: str, part: str) -> str | None:
    low = header_rest.lower()
    for kind, words in PART_TYPE_WORDS:
        if any(w in low for w in words):
            return kind
    return None


def split(lines: list[Line]) -> SplitResult:
    has_cau = any(QUESTION_RE.match(strip_markup(l.text).strip()) for l in lines)
    mode = "body"
    part: str | None = None
    part_types: dict[str | None, str] = {}
    blocks: list[_Block] = []
    key_lines: list[tuple[str | None, str]] = []
    preamble: list[str] = []
    warnings: list[str] = []
    seen: dict[tuple[str | None, int], int] = {}
    last_number: dict[str | None, int] = {}
    cau_parts: set[tuple[str, str | None]] = set()  # (mode, part) that use "Câu N" headers
    parts_seen: set[str] = set()
    in_key_table = False
    closed = False  # after "HẾT" or a repeated exam header, until the next question / part / section

    for line in lines:
        line = _fix_lookalikes(line)
        plain = strip_markup(line.text).strip()
        if not plain:
            continue
        cells = _cells(plain)
        if in_key_table and "|" in plain:
            key_lines.append((part, line.text))
            continue
        in_key_table = False
        if mode != "key" and _key_row(plain):
            key_lines.append((part, line.text))
            continue
        if _boundary(plain) and not QUESTION_RE.match(plain) and not _is_key_header_row(cells):
            closed = True
            preamble.append(line.text)
            continue
        if _is_key_header_row(cells):
            # an answer table inside the exam or its solutions (official files put one under each PHẦN)
            key_lines.append((part, line.text))
            in_key_table = True
            continue
        pm = PART_RE.match(plain)
        if pm and len(plain) <= 250:
            closed = False
            part = _part_label(pm.group(1))
            parts_seen.add(part)
            kind = _part_type(pm.group(2), part)
            if kind and mode == "body":
                part_types[part] = kind
            if mode == "key":
                key_lines.append((part, plain))
            continue
        if KEY_HEADER_RE.match(plain):
            mode, closed = "key", False
            continue
        if SOLUTION_SECTION_RE.match(plain):
            mode, part, closed = "solutions", None, False
            continue
        cau = QUESTION_RE.match(plain)
        if cau:
            cau_parts.add((mode, part))
        qm = cau or _numbered(plain, has_cau, (mode, part) in cau_parts, last_number.get(part, 0) if mode == "body" else None)
        if qm and mode == "key" and _looks_like_key(plain):
            key_lines.append((part, line.text))
            continue
        if qm and mode == "key":
            # the key section is over: questions again (a solution pass when already seen)
            mode = "solutions" if any(k[1] == int(qm.group(1)) for k in seen) else "body"
        if qm and mode != "key":
            closed = False
            n = int(qm.group(1))
            if mode == "body" and (part, n) in seen and n <= last_number.get(part, 0):
                # numbering restarted without a header: a trailing solutions section
                mode = "solutions"
            rest = QUESTION_RAW_RE.sub("", line.text.strip(), count=1) if cau else NUMBERED_RE.sub("", line.text.strip(), count=1)
            first = [Line(rest, line.page, line.ocr, line.confidence)] if strip_markup(rest).strip() else []
            if mode == "solutions":
                blocks.append(_Block(part, n, first, "solution"))
            else:
                blocks.append(_Block(part, n, first))
                seen[(part, n)] = len(blocks) - 1
                last_number[part] = max(last_number.get(part, 0), n)
            continue
        if mode == "key":
            key_lines.append((part, line.text))
            continue
        if blocks and not closed:
            blocks[-1].lines.append(line)
        else:
            preamble.append(line.text)

    if {"1", "2"} <= parts_seen:  # THPT 2025 layout: parts without type words follow the standard
        for p, kind in THPT_PART_TYPES.items():
            if p in parts_seen:
                part_types.setdefault(p, kind)

    questions: dict[tuple[str | None, int], ParsedQuestion] = {}
    order: list[tuple[str | None, int]] = []
    for b in blocks:
        if b.kind != "question":
            continue
        q = _parse_block(b, part_types.get(b.part))
        k = (b.part, b.number)
        if k in questions:
            warnings.append(f"Câu {b.number} xuất hiện nhiều lần")
            continue
        questions[k] = q
        order.append(k)

    for b in blocks:
        if b.kind != "solution":
            continue
        k = (b.part, b.number) if (b.part, b.number) in questions else _find_by_number(questions, b.number)
        if k is None:
            warnings.append(f"Lời giải câu {b.number} không khớp câu hỏi nào")
            continue
        _attach_solution(questions[k], b.lines, part_types.get(questions[k].part))

    key = _parse_key(key_lines, part_types)
    for k, value in key.items():
        target = k if k in questions else _find_by_number(questions, k[1])
        if target is None:
            continue
        q = questions[target]
        if q.answer is None:
            q.answer, q.answer_source = _answer_from_key(q, value), "key"
        elif not _same_as_key(q, value):
            q.issues.append("đáp án không khớp bảng đáp án")

    result = [questions[k] for k in order]
    _flag_odd_essays(result, part_types)
    for q in result:
        _finalise(q)
    return SplitResult(questions=result, preamble=preamble, warnings=warnings)


def _fix_lookalikes(line: Line) -> Line:
    if not any(c in line.text for c in LOOKALIKES):
        return line
    text = LOOKALIKE_LABEL_RE.sub(lambda m: LOOKALIKES[m.group(1)], line.text)
    return line if text == line.text else Line(text, line.page, line.ocr, line.confidence, line.meta)


KEY_ENTRY_RE = re.compile(r"^(?:(?:Câu\s*)?\d{1,3}\s*[:.)\-]?\s*(?:(?:[a-d]\)?\s*[:\-]?\s*(?:Đúng|Sai|Đ|S|Ð)\s*[,;]?\s*){1,4}|[ĐSÐ]{4}|[A-D]|-?\d+(?:[.,]\d+)?(?:/\d+)?)\s*[,;|]?\s*)+$", re.U)  # noqa: E501


def _looks_like_key(plain: str) -> bool:
    """"Câu 1: a) Đ b) S …", "Câu 1: 1 Câu 2: 4", "1.A 2.C" — answers, not a question."""
    return len(plain) <= 160 and bool(KEY_ENTRY_RE.match(plain))


def _cells(plain: str) -> list[str]:
    return [c.strip() for c in plain.split("|")] if "|" in plain else [plain]


def _is_key_header_row(cells: list[str]) -> bool:
    """"Câu | 1 | 2 …", "Mã đề | Câu 1 | …", or only "Câu 1 | Câu 2 | … " cells."""
    rest = [c for c in cells[1:] if c]
    if len(cells) >= 2 and KEY_ROW_HEAD_RE.match(cells[0]) and rest and all(_is_key_header_cell(c) for c in rest):
        return True
    named = [c for c in cells if c]
    return len(named) >= 2 and all(re.fullmatch(r"Câu\s*\d{1,3}", c, re.I | re.U) for c in named)


def _is_key_header_cell(c: str) -> bool:
    return bool(re.fullmatch(r"(?:Câu\s*)?\d{1,3}|[a-d]\)?|", c, re.I | re.U))


def _numbered(plain: str, has_cau: bool, part_uses_cau: bool, last: int | None):
    """Bare "N." headers: in files without "Câu", or in a part that numbers its questions that way
    (Word auto-numbering) — then only the next number counts, so lists inside a stem stay text."""
    m = NUMBERED_RE.match(plain)
    if not m or not has_cau:
        return m
    if part_uses_cau or last is None or int(m.group(1)) != last + 1:
        return None
    return m


def _flag_odd_essays(result: list[ParsedQuestion], part_types: dict) -> None:
    """An 'essay' inside a mostly-MCQ part is usually an MCQ whose options we failed to read."""
    by_part: dict[str | None, list[ParsedQuestion]] = {}
    for q in result:
        by_part.setdefault(q.part, []).append(q)
    for part, qs in by_part.items():
        if part_types.get(part) == "essay":
            continue
        mcq = sum(q.type == "mcq" for q in qs)
        mostly_mcq = mcq and mcq / len(qs) >= 0.5
        for q in qs:
            if q.type == "essay" and (mostly_mcq or CHOICE_WORDS_RE.search(strip_markup(q.stem))):
                q.issues.append("không nhận ra phương án")


def _find_by_number(questions, n):
    matches = [k for k in questions if k[1] == n]
    return matches[0] if len(matches) == 1 else None


def _strong_labels(text: str, expected: str) -> list[str]:
    """Labels whose marker or content is underlined/highlighted — stronger than bold, which some
    files put on every label."""
    matches = [m for m in OPTION_RE.finditer(text)]
    out = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if re.search(r"\{\.(?:underline|mark)\}", text[m.start():end]) or (m.start() > 0 and text[m.start() - 1] == "["):
            out.append(m.group("label"))
    return out


def _find_options(text: str, expected: str) -> list[tuple[str, str, bool]]:
    """Split a line into (label, content, emphasised) when it starts with the expected option label."""
    matches = list(OPTION_RE.finditer(text))
    lead = len(text) - len(text.lstrip())
    if not matches or matches[0].start() not in (lead, lead + 1) or matches[0].group("label") != expected \
            or (matches[0].start() == lead + 1 and text[lead] != "["):
        return []
    picked = [matches[0]]
    for m in matches[1:]:
        if ord(m.group("label")) == ord(picked[-1].group("label")) + 1:
            picked.append(m)
    out = []
    for i, m in enumerate(picked):
        end = picked[i + 1].start() if i + 1 < len(picked) else len(text)
        content = text[m.end():end].strip().strip("|").strip()
        if i + 1 < len(picked) and content.endswith("["):
            content = content[:-1].strip()  # "[" opening a highlight around the next option
        mark = m.group("mark")
        emphasised = is_emphasised_label(mark)
        wrapped = m.start() > 0 and text[m.start() - 1] == "["  # "[**C.** 3]{.mark}"
        if wrapped and re.search(r"\]\{\.(?:underline|mark)\}", content):
            emphasised = True
            content = re.sub(r"\]\{\.(?:underline|mark)\}", "", content, count=1).strip()
        # the wrapper may span the whole option: "[C. 3]{.underline}", "**C. 3**"
        elif not emphasised and mark.startswith("[") and re.search(r"\]\{\.(?:underline|mark)\}", content):
            emphasised = True
            content = re.sub(r"\]\{\.(?:underline|mark)\}", "", content, count=1).strip()
        elif not emphasised and mark.startswith("**") and content.count("**") % 2 == 1:
            emphasised = True
            content = content.replace("**", "", 1).strip() if content.startswith("**") else content[::-1].replace("**", "", 1)[::-1].strip()
        out.append((m.group("label"), content, emphasised))
    return out


def _parse_block(b: _Block, part_type: str | None) -> ParsedQuestion:
    q = ParsedQuestion(number=b.number, part=b.part)
    q.raw = "\n".join(l.text for l in b.lines)
    q.pages = sorted({l.page for l in b.lines if l.page is not None})
    q.ocr = any(l.ocr for l in b.lines)
    stem: list[str] = []
    options: dict[str, list[str]] = {}
    statements: dict[str, list[str]] = {}
    solution: list[str] = []
    marked: list[str] = []
    state = "stem"
    last_label: str | None = None
    short_value: str | None = None

    for line in b.lines:
        text = line.text.strip()
        plain = strip_markup(text).strip()
        if not plain:
            continue
        if EMPTY_ANSWER_RE.match(plain) and (options or statements):
            state = "solution"  # "Đáp án:" alone, the answer (e.g. an a|b|c|d grid) follows
            continue
        hm = SOLUTION_HEAD_RE.match(plain)
        if hm:
            state = "solution"
            rest = plain[hm.end():].strip()
            solution.append(f"**{hm.group(1)}:**" + (f" {rest}" if rest else ""))
            continue
        sm = SOLUTION_START_RE.match(plain)
        if sm and state != "solution":
            state = "solution"
            rest = plain[sm.end():].strip()
            if rest:
                solution.append(rest)
            continue
        if state == "solution":
            solution.append(text)
            continue
        ia = INLINE_ANSWER_RE.match(plain)
        if ia and (options or part_type in (None, "mcq")):
            q.answer, q.answer_source = {"key": ia.group(1)}, "inline"
            continue
        sa = SHORT_ANSWER_RE.match(plain)
        if sa and not options and not statements:
            short_value = short_value_of(sa.group(1))
            continue
        expected = chr(ord(last_label) + 1) if last_label and last_label in "ABC" and state == "options" else "A"
        opts = _find_options(text, expected) if part_type != "true_false" else []
        if opts:
            state = "options"
            for label, content, emph in opts:
                options[label] = [content] if content else []
                if emph:
                    marked.append(label)
                last_label = label
            continue
        tf = TF_STATEMENT_RE.match(text) if part_type in (None, "true_false") and not options else None
        if tf and (part_type == "true_false" or tf.group(1) == "a" or statements):
            label = tf.group(1)
            if not statements and label != "a":
                tf = None
            else:
                state = "statements"
                statements[label] = [tf.group(2).strip()]
                last_label = label
                continue
        if state == "options" and last_label:
            options[last_label].append(text)
        elif state == "statements" and last_label:
            statements[last_label].append(text)
        else:
            stem.append(text)

    q.stem = "\n\n".join(stem).strip()
    q.solution = "\n\n".join(solution).strip()
    q.marked_labels = marked

    if statements:
        q.type = "true_false"
        q.options = [{"label": k, "content": "\n\n".join(v).strip(), "is_true": None} for k, v in sorted(statements.items())]
        verdicts = _verdicts(q.solution)
        if len(verdicts) >= len(q.options) and q.options:
            _apply_tf(q, verdicts, "inline")
    elif options:
        q.type = "mcq"
        q.options = [{"label": k, "content": "\n\n".join(v).strip()} for k, v in sorted(options.items())]
    else:
        q.type = part_type if part_type in ("short_answer", "essay") else ("short_answer" if short_value else "essay")

    if part_type == "short_answer" and q.type != "short_answer" and not q.options:
        q.type = "short_answer"
    if q.type == "short_answer" and short_value:
        q.answer, q.answer_source = {"value": short_value}, "inline"
    if q.type == "mcq" and q.answer is None:
        m = CHOOSE_IN_TEXT_RE.search(strip_markup(q.solution))
        if m:
            q.answer, q.answer_source = {"key": m.group(1)}, "inline"
        elif len(marked) == 1 and len(options) > 1:
            q.answer, q.answer_source = {"key": marked[0]}, "format"
    return q


def _apply_tf(q: ParsedQuestion, verdicts: dict[str, bool], source: str) -> None:
    for o in q.options:
        if o["label"] in verdicts:
            o["is_true"] = verdicts[o["label"]]
    q.answer, q.answer_source = {o["label"]: o["is_true"] for o in q.options}, source


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", strip_markup(text)).strip()


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", strip_markup(text))


def _option_line(text: str):
    """The first option marker when a line starts with one (possibly inside "[" of a highlight)."""
    t = text.strip()
    m = OPTION_RE.search(t)
    return m if m and (m.start() == 0 or (m.start() == 1 and t[0] == "[")) else None


def _copy_end(lines: list[Line], qtype: str) -> int:
    """Index of the last line of the copied question (its options / d) statement), or -1.

    Only lines before the first solution heading count, so a block that starts straight with the
    solution keeps all of it."""
    last = -1
    for i, l in enumerate(lines):
        plain = strip_markup(l.text).strip()
        if SOLUTION_START_RE.match(plain) or SOLUTION_HEAD_RE.match(plain) or INLINE_ANSWER_RE.match(plain):
            break
        if qtype == "mcq" and _option_line(l.text):
            last = i
        elif qtype == "true_false" and TF_STATEMENT_RE.match(l.text.strip()) and not TF_VERDICT_RE.match(plain):
            last = i
    return last


def _verdicts(text: str) -> dict[str, bool]:
    """Statement verdicts written in a solution: "a) Đúng", "a đúng| b sai", or an a|b|c|d grid."""
    plain = strip_markup(text)
    v = r"(Đúng|Sai|ĐÚNG|SAI|đúng|sai|Đ|S|Ð)"
    grid = re.search(r"(?m)^[ \t]*a\)?[ \t]*\|[ \t]*b\)?[ \t]*\|[ \t]*c\)?[ \t]*\|[ \t]*d\)?[ \t]*\n+[ \t]*" +
                     r"[ \t]*\|[ \t]*".join([v] * 4) + r"[ \t]*$", plain)
    if grid:
        return {k: x[0].upper() in ("Đ", "Ð") for k, x in zip("abcd", grid.groups())}
    out: dict[str, bool] = {}
    for m in TF_VERDICT_RE.finditer(plain):
        out.setdefault(m.group(1), m.group(2)[0].upper() in ("Đ", "Ð"))
    return out


def short_value_of(raw: str) -> str:
    """"$45^{\\circ}$." → "45", "25 (gam/lít)." → "25", "-1,5" stays; other text is kept trimmed."""
    v = raw.strip().strip("*").strip()
    # LaTeX around numbers: "$4\\text{,}39$", "$-\\frac{1}{2}$" stays as text, "$45^{\\circ}$"
    v = re.sub(r"\\text\{([^{}]*)\}", r"\1", v).replace("{,}", ",").replace("\\,", "").replace("\\!", "")
    num = re.match(r"^\$?\s*(-?\d+(?:[.,]\d+)?(?:/\d+)?)", v.replace("−", "-"))
    if num:
        return num.group(1)
    return v.rstrip(".").strip()


def _attach_solution(q: ParsedQuestion, lines: list[Line], part_type: str | None = None) -> None:
    """Merge a solution-section block into its question.

    Official files copy the whole question (stem, options with the key highlighted, statements)
    before the solution; lines that repeat the question are dropped, and a single highlighted
    option in the copy is read as the answer.
    """
    asked = {_squash(x) for x in q.raw.split("\n") if _squash(x)}
    copy_end = _copy_end(lines, q.type)
    body: list[str] = []
    strong_marks: list[str] = []  # underlined / highlighted in the copy
    bold_marks: list[str] = []
    for i, l in enumerate(lines):
        plain = strip_markup(l.text).strip()
        if not plain:
            continue
        if i <= copy_end:  # the question copied again before its solution
            if q.type == "mcq" and _option_line(l.text):
                opts = _find_options(l.text.strip(), _option_line(l.text).group("label"))
                strong_marks += _strong_labels(l.text.strip(), "A")
                bold_marks += [label for label, _, emph in opts if emph]
            ia = INLINE_ANSWER_RE.match(plain)
            if not ia:
                continue
        elif not body and _squash(l.text) in asked:
            continue
        ia = INLINE_ANSWER_RE.match(plain)
        if ia and q.type == "mcq":
            if q.answer is None or q.answer_source in ("format", "key"):
                q.answer, q.answer_source = {"key": ia.group(1)}, "inline"
            continue
        hm = SOLUTION_HEAD_RE.match(plain)
        if hm:
            rest = plain[hm.end():].strip()
            body.append(f"**{hm.group(1)}:**" + (f" {rest}" if rest else ""))
            continue
        sm = SOLUTION_START_RE.match(plain)
        if sm:
            rest = plain[sm.end():].strip()
            if rest:
                body.append(rest)
            continue
        body.append(l.text.strip())
    text = "\n\n".join(body).strip()
    q.solution = (q.solution + "\n\n" + text).strip() if q.solution else text
    if q.type == "mcq" and q.answer is None:
        m = CHOOSE_IN_TEXT_RE.search(strip_markup(text))
        if m:
            q.answer, q.answer_source = {"key": m.group(1)}, "inline"
        else:
            marks = set(strong_marks) or set(bold_marks)
            if len(marks) == 1:
                q.answer, q.answer_source = {"key": marks.pop()}, "format"
    if q.type == "true_false" and (q.answer is None or any(o.get("is_true") is None for o in q.options)):
        verdicts = _verdicts(text)
        if len(verdicts) >= len(q.options) and q.options:
            _apply_tf(q, verdicts, "inline")
    if q.type == "short_answer" and q.answer is None:
        for l in body:
            sa = SHORT_ANSWER_RE.match(strip_markup(l).strip())
            if sa and short_value_of(sa.group(1)):
                q.answer, q.answer_source = {"value": short_value_of(sa.group(1))}, "inline"
                break


KEY_PAIR_RE = re.compile(r"(?:Câu\s*)?(\d{1,3})\s*[.\-:)]?\s*([A-D])(?![A-Za-zÀ-ỹ])", re.U)
KEY_TF_RE = re.compile(r"(?:Câu\s*)?(\d{1,3})\s*[.\-:)]\s*((?:[a-d]\s*\)?\s*[:\-]?\s*(?:Đúng|Sai|Đ|S)\s*[,;]?\s*){2,4}|[ĐS]{4})", re.U)
KEY_SHORT_RE = re.compile(r"(?:Câu\s*)?(\d{1,3})\s*[.:)]\s*(-?\d+(?:[.,]\d+)?(?:/\d+)?)", re.U)


ANSWER_LABEL_RE = re.compile(r"^(?:đáp\s+án|đa|trả\s+lời|kết\s+quả|chọn)$", re.I | re.U)


def _parse_key(key_lines: list[tuple[str | None, str]], part_types: dict) -> dict[tuple[str | None, int], object]:
    """Answer keys: "1.A 2.C", or tables — a header row of question numbers (or a)–d) for a
    true/false grid) followed by value rows, per part."""
    out: dict[tuple[str | None, int], object] = {}
    header: list[str] | None = None
    for part, raw in key_lines:
        text = strip_markup(raw).replace("Ð", "Đ")
        kind = part_types.get(part, "mcq")
        tabular = "|" in text or "\t" in text
        cells = [c.strip() for c in re.split(r"\s*\|\s*|\t+", text)] if tabular else text.split()
        if not tabular:  # PDF tables arrive as words: "Câu 1 2 3 …" / "Đáp án D D B …"
            lm = re.match(r"^(câu|đáp\s+án|trả\s+lời|mã\s+đề|kết\s+quả)(?=\s)\s*", text.strip(), re.I | re.U)
            if lm:
                cells, tabular = [lm.group(1)] + text.strip()[lm.end():].split(), True
        label = cells[0] if cells else ""
        if header and header[0].startswith("tf:"):  # grid rows: "1 | S | Đ | S | Đ"
            row = [c for c in cells if c]
            if len(row) == len(header) + 1 and re.fullmatch(r"\d{1,3}", row[0]):
                out[(part, int(row[0]))] = {h[3]: v.upper().startswith("Đ") for h, v in zip(header, row[1:])}
                continue
            header = None
        labelled = label == "" or ANSWER_LABEL_RE.match(label)
        values = cells[1:] if labelled else cells
        if header and tabular and (labelled or len([c for c in cells if c]) == len(header)):
            for n, v in zip(header, values):
                if n and v and v not in ("_", "-"):
                    value = _key_value(kind, v)
                    if value is not None:
                        out[(part, int(n))] = value
            header = None
            continue
        body = cells[1:] if tabular and (label == "" or KEY_LABEL_RE.match(label)) else cells
        body = [c for c in body if c]
        if tabular and body and (len(body) >= 2 or KEY_ROW_HEAD_RE.match(label)) and all(re.fullmatch(r"(?:Câu\s*)?\d{1,3}", c, re.I) for c in body):
            header = [re.sub(r"\D", "", c) for c in body]
            continue
        if tabular and len(body) >= 2 and all(re.fullmatch(r"[a-d]\)?", c) for c in body):
            header = ["tf:" + c[0] for c in body]
            continue
        header = None
        if kind == "true_false":
            for m in KEY_TF_RE.finditer(text):
                out[(part, int(m.group(1)))] = _tf_verdicts(m.group(2))
            continue
        if kind == "short_answer":
            for m in KEY_SHORT_RE.finditer(text):
                out[(part, int(m.group(1)))] = m.group(2)
            continue
        for m in KEY_PAIR_RE.finditer(text):
            out[(part, int(m.group(1)))] = m.group(2)
    return out


def _same_as_key(q: ParsedQuestion, value) -> bool:
    if q.type == "mcq":
        return q.answer.get("key") == value
    if q.type == "true_false" and isinstance(value, dict):
        return all(q.answer.get(k) is v for k, v in value.items())
    if q.type == "short_answer":
        return same_short_answer(str(value), str(q.answer.get("value", "")))
    return True


def _key_value(kind: str, v: str):
    if kind == "true_false":
        verdicts = _tf_verdicts(v)
        return verdicts if len(verdicts) == 4 and all(isinstance(x, bool) for x in verdicts.values()) else None
    if kind == "short_answer":
        return short_value_of(v) or None
    return v if re.fullmatch(r"[A-D]", v) else None


def _tf_verdicts(s: str) -> dict[str, bool]:
    s = s.replace("Ð", "Đ")
    items = TF_VERDICT_RE.findall(s)
    if items:
        return {k: v[0].upper() == "Đ" for k, v in items}
    letters = re.sub(r"[^ĐS]", "", s.upper())
    return {chr(ord("a") + i): ch == "Đ" for i, ch in enumerate(letters[:4])} if len(letters) == 4 else {}


def _answer_from_key(q: ParsedQuestion, value) -> dict:
    if q.type == "true_false" and isinstance(value, dict):
        for o in q.options:
            if o["label"] in value:
                o["is_true"] = value[o["label"]]
        return {o["label"]: o.get("is_true") for o in q.options}
    if q.type == "short_answer":
        return {"value": str(value)}
    return {"key": str(value)}


def _finalise(q: ParsedQuestion) -> None:
    extra = list(q.issues)
    if q.type == "mcq":
        n = len(q.options)
        if 1 < len(q.marked_labels) < n:  # all labels styled alike is decoration, not an answer
            extra.append("nhiều phương án được đánh dấu")
        if q.answer and q.answer_source != "format" and len(q.marked_labels) == 1 and q.marked_labels[0] != q.answer.get("key"):
            extra.append("đáp án không khớp định dạng")
    q.issues, q.confidence = evaluate(q.type, q.stem, q.options, q.answer, q.solution, extra_issues=extra, ocr=q.ocr)
