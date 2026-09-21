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

from app.ingestion.lines import Line, is_emphasised_label, strip_markup

AUTO_APPROVE_DEFAULT = 0.85

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
_HDR_WORDS = r"(?:Câu|CÂU|Bài|BÀI|Question|QUESTION)"
QUESTION_RE = re.compile(rf"^{_HDR_WORDS}\s*(\d{{1,3}})\s*(?:\(([^)]*)\))?\s*[.:)]?\s*", re.U)
# Same header, tolerant of our emphasis markup around it, used to cut it off the raw text.
QUESTION_RAW_RE = re.compile(rf"^(?:\*\*|__)?\s*{_HDR_WORDS}\s*\d{{1,3}}\s*(?:\([^)]*\))?\s*[.:)]?\s*(?:\*\*|__)?\s*[.:]?\s*", re.U)
NUMBERED_RE = re.compile(r"^(\d{1,3})\s*[.)]\s+(?=\S)")
PART_RE = re.compile(r"^(?:PHẦN|Phần)\s+(I{1,3}|IV|V|[1-5])\b\s*[.:]?\s*(.*)$", re.U)
KEY_HEADER_RE = re.compile(r"^(?:BẢNG\s+ĐÁP\s+ÁN|ĐÁP\s+ÁN(?:\s+THAM\s+KHẢO)?|Bảng\s+đáp\s+án|Đáp\s+án\s+tham\s+khảo)\s*[.:]?\s*$", re.U)
# Upper-case only: "Lời giải" in mixed case starts a per-question solution, not a section.
SOLUTION_SECTION_RE = re.compile(
    r"^(?:HƯỚNG\s+DẪN\s+GIẢI|LỜI\s+GIẢI|ĐÁP\s+ÁN\s+VÀ\s+(?:HƯỚNG\s+DẪN\s+GIẢI|LỜI\s+GIẢI))(?:\s+CHI\s+TIẾT)?\s*[.:]?\s*$", re.U)
SOLUTION_START_RE = re.compile(r"^(?:Lời\s+giải|Hướng\s+dẫn\s+giải|Hướng\s+dẫn|Giải|LỜI\s+GIẢI)(?:\s+chi\s+tiết)?\s*(?:[.:]\s*|$)", re.U | re.I)
INLINE_ANSWER_RE = re.compile(r"^(?:Đáp\s+án|Chọn|ĐÁP\s+ÁN|CHỌN)(?:\s+đúng)?\s*[:.]?\s*(?:đáp\s+án\s+)?([A-D])(?=[\s.,;]|$)", re.U)
CHOOSE_IN_TEXT_RE = re.compile(r"(?:Chọn|chọn|CHỌN)\s+(?:đáp\s+án\s+|phương\s+án\s+)?([A-D])(?=[\s.,;)]|$)", re.U)
SHORT_ANSWER_RE = re.compile(r"^(?:Đáp\s+án|Đáp\s+số|Trả\s+lời|Kết\s+quả|ĐÁP\s+ÁN|ĐÁP\s+SỐ)\s*[:.]\s*(.+)$", re.U)
TF_STATEMENT_RE = re.compile(r"^(?:\*\*)?([a-d])\s*[).]\s*(?:\*\*)?\s*(.*)$", re.U)
TF_VERDICT_RE = re.compile(r"([a-d])\s*[).]?\s*[:\-–]?\s*(Đúng|Sai|ĐÚNG|SAI|Đ|S)(?![A-Za-zÀ-ỹ])", re.U)
# An option marker: optional emphasis, a capital A–D, "." or ")", optional emphasis, then space/end.
OPTION_RE = re.compile(
    r"(?:(?<=^)|(?<=\s)|(?<=\|))"
    r"(?P<mark>(?:\*\*)?(?:\[)?(?P<label>[A-D])(?P<delim>[.)])(?:\]\{\.(?:underline|mark)\})?(?:\*\*)?)"
    # a space normally follows the label; OCR often drops it ("D.14", "B.(2;1)")
    r"(?=\s|$|(?<=[.)])(?=[^\s.,;:]))", re.U)

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

    for line in lines:
        plain = strip_markup(line.text).strip()
        if not plain:
            continue
        pm = PART_RE.match(plain)
        if pm and len(plain) <= 250:
            part = _part_label(pm.group(1))
            kind = _part_type(pm.group(2), part)
            if kind and mode == "body":
                part_types[part] = kind
            if mode == "key":
                key_lines.append((part, plain))
            continue
        if KEY_HEADER_RE.match(plain):
            mode = "key"
            continue
        if SOLUTION_SECTION_RE.match(plain):
            mode, part = "solutions", None
            continue
        qm = QUESTION_RE.match(plain) or (None if has_cau else NUMBERED_RE.match(plain))
        if qm and mode != "key":
            n = int(qm.group(1))
            if mode == "body" and (part, n) in seen and n <= last_number.get(part, 0):
                # numbering restarted without a header: a trailing solutions section
                mode = "solutions"
            rest = QUESTION_RAW_RE.sub("", line.text.strip(), count=1) if has_cau else NUMBERED_RE.sub("", line.text.strip(), count=1)
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
        if blocks:
            blocks[-1].lines.append(line)
        else:
            preamble.append(line.text)

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
        _attach_solution(questions[k], b.lines)

    key = _parse_key(key_lines, part_types)
    for k, value in key.items():
        target = k if k in questions else _find_by_number(questions, k[1])
        if target is None:
            continue
        q = questions[target]
        if q.answer is None:
            q.answer, q.answer_source = _answer_from_key(q, value), "key"
        elif q.type == "mcq" and q.answer.get("key") != value:
            q.issues.append("đáp án không khớp bảng đáp án")

    result = [questions[k] for k in order]
    _flag_odd_essays(result, part_types)
    for q in result:
        _finalise(q)
    return SplitResult(questions=result, preamble=preamble, warnings=warnings)


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


def _find_options(text: str, expected: str) -> list[tuple[str, str, bool]]:
    """Split a line into (label, content, emphasised) when it starts with the expected option label."""
    matches = list(OPTION_RE.finditer(text))
    if not matches or matches[0].start() != len(text) - len(text.lstrip()) or matches[0].group("label") != expected:
        return []
    picked = [matches[0]]
    for m in matches[1:]:
        if ord(m.group("label")) == ord(picked[-1].group("label")) + 1:
            picked.append(m)
    out = []
    for i, m in enumerate(picked):
        end = picked[i + 1].start() if i + 1 < len(picked) else len(text)
        content = text[m.end():end].strip().strip("|").strip()
        mark = m.group("mark")
        emphasised = is_emphasised_label(mark)
        # the wrapper may span the whole option: "[C. 3]{.underline}", "**C. 3**"
        if not emphasised and mark.startswith("[") and re.search(r"\]\{\.(?:underline|mark)\}", content):
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
            short_value = sa.group(1).strip()
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
        verdicts = {m.group(1): m.group(2).upper().startswith("Đ") for m in TF_VERDICT_RE.finditer(strip_markup(q.solution))}
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


def _attach_solution(q: ParsedQuestion, lines: list[Line]) -> None:
    body: list[str] = []
    for l in lines:
        plain = strip_markup(l.text).strip()
        if not plain:
            continue
        ia = INLINE_ANSWER_RE.match(plain)
        if ia and q.type == "mcq" and q.answer is None:
            q.answer, q.answer_source = {"key": ia.group(1)}, "inline"
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
    if q.type == "true_false" and (q.answer is None or any(o.get("is_true") is None for o in q.options)):
        verdicts = {m.group(1): m.group(2).upper().startswith("Đ") for m in TF_VERDICT_RE.finditer(strip_markup(text))}
        if len(verdicts) >= len(q.options) and q.options:
            _apply_tf(q, verdicts, "inline")
    if q.type == "short_answer" and q.answer is None:
        for l in body:
            sa = SHORT_ANSWER_RE.match(strip_markup(l))
            if sa:
                q.answer, q.answer_source = {"value": sa.group(1).strip()}, "inline"


KEY_PAIR_RE = re.compile(r"(?:Câu\s*)?(\d{1,3})\s*[.\-:)]?\s*([A-D])(?![A-Za-zÀ-ỹ])", re.U)
KEY_TF_RE = re.compile(r"(?:Câu\s*)?(\d{1,3})\s*[.\-:)]\s*((?:[a-d]\s*\)?\s*[:\-]?\s*(?:Đúng|Sai|Đ|S)\s*[,;]?\s*){2,4}|[ĐS]{4})", re.U)
KEY_SHORT_RE = re.compile(r"(?:Câu\s*)?(\d{1,3})\s*[.:)]\s*(-?\d+(?:[.,]\d+)?(?:/\d+)?)", re.U)


def _parse_key(key_lines: list[tuple[str | None, str]], part_types: dict) -> dict[tuple[str | None, int], object]:
    out: dict[tuple[str | None, int], object] = {}
    pending_numbers: list[int] | None = None
    for part, raw in key_lines:
        text = strip_markup(raw)
        kind = part_types.get(part, "mcq")
        cells = [c.strip() for c in re.split(r"\s*\|\s*|\t+", text) if c.strip()]
        if len(cells) == 1:  # PDF tables arrive as space-separated words
            cells = cells[0].split()
        while cells and not re.fullmatch(r"\d{1,3}", cells[0]) and not re.fullmatch(r"[A-D]", cells[0]):
            cells = cells[1:]  # row label such as "Câu" / "Đáp án"
        if cells and all(re.fullmatch(r"\d{1,3}", c) for c in cells) and len(cells) >= 2:
            pending_numbers = [int(c) for c in cells]
            continue
        if pending_numbers and cells and all(re.fullmatch(r"[A-D]", c) for c in cells):
            for n, v in zip(pending_numbers, cells):
                out[(part, n)] = v
            pending_numbers = None
            continue
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


def _tf_verdicts(s: str) -> dict[str, bool]:
    items = TF_VERDICT_RE.findall(s)
    if items:
        return {k: v.upper().startswith("Đ") for k, v in items}
    return {chr(ord("a") + i): ch == "Đ" for i, ch in enumerate(s[:4])}


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
    from app.services.question_quality import evaluate

    extra = list(q.issues)
    if q.type == "mcq":
        n = len(q.options)
        if 1 < len(q.marked_labels) < n:  # all labels styled alike is decoration, not an answer
            extra.append("nhiều phương án được đánh dấu")
        if q.answer and q.answer_source != "format" and len(q.marked_labels) == 1 and q.marked_labels[0] != q.answer.get("key"):
            extra.append("đáp án không khớp định dạng")
    q.issues, q.confidence = evaluate(q.type, q.stem, q.options, q.answer, q.solution, extra_issues=extra, ocr=q.ocr)
