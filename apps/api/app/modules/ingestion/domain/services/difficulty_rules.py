"""Where a question's level comes from when nothing has read the question (difficulty-at-upload ADR-02): its place
in the paper. THPT 2025 papers are written to a fixed shape — PHẦN I trắc nghiệm, PHẦN II đúng/sai, PHẦN III trả
lời ngắn — and inside each part the questions are ordered easy first. `part` and `number` are on every parsed
question before anything else runs, so this costs nothing and never fails.

It is a **convention, not a reading**: it says what a paper of this shape usually puts at that position, not what
this particular question asks. That is why the model leads where it answers (A-05) and this only fills the rest —
but it fills *every* rest, because an empty level is the problem the feature exists to solve.

The model's half — the prompt and the reading of its reply — sits here too, the way `topic_rules` holds the
tagging prompt: one wording, and one place where a reply becomes a level.
"""
import unicodedata

from app.modules.ingestion.domain.services.ai_parse import parse_json

# (last number of the band, level) per part, in order; past the last band the level stays the highest one named.
# Phần I — 12 multiple-choice questions, four options, the part every candidate is meant to finish:
#   ≤6   nb  the first half is recall — a definition, a formula, a value read straight off a graph or a table
#   ≤10  th  câu 7–10 still resolve in one transformation, but the answer is not written in the stem
#   >10  vd  câu 11–12 close the part and are where it starts to separate candidates
# Phần II — 4 true/false questions, each four statements about one setting. All four must be right for full marks,
# so the part never starts at nhận biết:
#   ≤2   th
#   >2   vd  câu 3–4. Never vdc: the statements are scored one by one, so partial credit keeps the ceiling lower
#            than Phần III's, where a wrong number scores nothing
# Phần III — 6 short-answer questions, no options to eliminate and no partial credit:
#   ≤3   vd  the floor of this part is already vận dụng
#   >3   vdc câu 4–6 are the last marks of the paper and the ones most candidates leave blank
BY_PART: dict[str, tuple[tuple[int, str], ...]] = {
    "1": ((6, "nb"), (10, "th"), (12, "vd")),
    "2": ((2, "th"), (4, "vd")),
    "3": ((3, "vd"), (6, "vdc")),
}

# A paper with no PHẦN headers (the 40-question papers, and most of what a teacher uploads) carries the same
# easy-first order over a part three times longer, so the bands stretch with it; the question type stands in for
# the part header it does not have.
#   mcq         ≤15 nb, ≤30 th, ≤37 vd, >37 vdc — a 40-câu paper spends its first ~40% on recall and keeps its
#               three or four hardest questions for the end
#   true_false  as Phần II: the type carries that convention on its own
#   short_answer as Phần III
#   essay       a written answer is the reasoning tail of a paper: vd, then vdc past the second one
BY_TYPE: dict[str, tuple[tuple[int, str], ...]] = {
    "mcq": ((15, "nb"), (30, "th"), (37, "vd"), (40, "vdc")),
    "true_false": BY_PART["2"],
    "short_answer": BY_PART["3"],
    "essay": ((2, "vd"), (4, "vdc")),
}


def difficulty_for(part: str | None, number: int | None, qtype: str) -> str:
    """The level the paper's shape implies for that position — always one of the four, never None (ADR-02)."""
    bands = BY_PART.get(part or "") or BY_TYPE.get(qtype) or BY_TYPE["mcq"]
    n = number or 1  # a question the splitter could not number is read as the first of its part, the mildest guess
    for last, level in bands:
        if n <= last:
            return level
    return bands[-1][1]


DIFFICULTY_SYSTEM = """Bạn xếp mức độ nhận thức cho câu hỏi toán THPT. Với MỖI câu hỏi trong yêu cầu, chọn MỘT
mức và trả về đúng mã của nó:
"nb" = nhận biết: nhắc lại định nghĩa, công thức, hoặc đọc thẳng một giá trị từ đề, hình, bảng.
"th" = thông hiểu: một bước biến đổi hoặc một lần áp dụng công thức là ra đáp số.
"vd" = vận dụng: nhiều bước, phải tự chọn hướng làm.
"vdc" = vận dụng cao: nhiều bước kết hợp nhiều chủ đề, hoặc lập luận dài, hoặc bài toán thực tế phải mô hình hóa.
Số phần tử trong "results" phải bằng đúng số câu hỏi được hỏi, theo đúng thứ tự, không bỏ sót câu nào; câu nào
không chắc thì vẫn chọn mức gần nhất. Trả về DUY NHẤT JSON:
{"results": [{"number": 1, "level": "nb"}, {"number": 2, "level": "vd"}]}."""

# One question per call, because a level asked in a batch of ten is not a property of the question. Measured on
# the owner's 376-question bank: two runs of the same batching agree on 99% of questions, two *different* batchings
# on 58% — the model compares the ten questions in front of it and converges on the middle label (vd 52% of the
# bank). Asked one at a time it agrees with itself on 100%, uses all four bands (vdc 6% → 28%), and the systematic
# per-part bias disappears (Phần III two-band disagreement 16% → 1%). It costs ~45% more time over the whole bank.
DIFFICULTY_BATCH = 1
DIFFICULTY_TEXT_CHARS = 1200  # of each question, stem and options together — see `question_text`

# The types whose options are part of the question rather than a listing beside it. For everything else the stem
# is the whole question and there is nothing to add.
TYPES_WITH_OPTIONS = ("mcq", "true_false")


def question_text(stem: str, qtype: str, options: list | None = None) -> str:
    """One question as the model is shown it: the stem, and for `TYPES_WITH_OPTIONS` the options under it.

    The first measurement of this pass sent the stem alone, and the two signals came apart by two bands or more
    on 47 of Phần I's 208 questions — with the model reading the question as *harder* in 42 of those 47. That is
    what a model judging a multiple-choice question without its options would do: asked to solve from scratch
    rather than to pick from four, it never sees the three distractors that make the answer obvious. A true/false
    question is the starker case — its stem is often only the setting, and all four statements are the work.

    **Which option is correct is never sent.** A model told the answer is not judging how hard the question is to
    answer any more, and `is_true` is the one field in a true/false option that would tell it.
    """
    if qtype not in TYPES_WITH_OPTIONS:
        return stem
    lines = [f"{o.get('label')}. {o.get('content')}".strip()
             for o in (options or []) if isinstance(o, dict) and o.get("content")]
    return "\n".join([stem, *lines]) if lines else stem

# A small model answers in the words of the prompt as often as in its codes, and "vận dụng cao" ends with the whole
# of "vận dụng" — so the reply is matched against the full label, never a prefix of one.
LEVEL_WORDS = {
    "nb": "nb", "nhận biết": "nb", "nhan biet": "nb",
    "th": "th", "thông hiểu": "th", "thong hieu": "th",
    "vd": "vd", "vận dụng": "vd", "van dung": "vd",
    "vdc": "vdc", "vận dụng cao": "vdc", "van dung cao": "vdc",
}


def difficulty_request(rows: list[tuple[int, str]]) -> str:
    """The user half of the prompt: one batch of questions, numbered for the answer to refer to."""
    qs = "\n\n".join(f"Câu {number}: {text[:DIFFICULTY_TEXT_CHARS]}" for number, text in rows)
    numbers = ", ".join(str(number) for number, _ in rows)
    # small models mirror the example and answer once for a whole batch: name the count and the numbers again
    return f"Trả về đúng {len(rows)} phần tử, cho các câu: {numbers}.\n\nCÂU HỎI:\n{qs}"


def read_difficulty_reply(text: str, keys: dict) -> dict:
    """What the model chose, as {caller key: level}; raises LlmError on an answer that is not JSON.
    The label is the answer here — there is no listing to index into — so anything that does not read as one of
    the four levels is dropped and the position rule keeps that question."""
    results = parse_json(text).get("results")
    out: dict = {}
    for r in results if isinstance(results, list) else []:
        try:
            key = keys[int(r["number"])]
        except (KeyError, TypeError, ValueError):
            continue
        level = _level(r.get("level"))
        if level is not None:
            out[key] = level
    return out


def _level(value) -> str | None:
    return LEVEL_WORDS.get(unicodedata.normalize("NFC", value).strip().lower()) if isinstance(value, str) else None
