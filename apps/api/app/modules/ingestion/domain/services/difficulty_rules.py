"""Where a question's level comes from when nothing has read the question (difficulty-at-upload ADR-02): its place
in the paper. THPT 2025 papers are written to a fixed shape — PHẦN I trắc nghiệm, PHẦN II đúng/sai, PHẦN III trả
lời ngắn — and inside each part the questions are ordered easy first. `part` and `number` are on every parsed
question before anything else runs, so this costs nothing and never fails.

It is a **convention, not a reading**: it says what a paper of this shape usually puts at that position, not what
this particular question asks. That is why the model leads where it answers (A-05) and this only fills the rest —
but it fills *every* rest, because an empty level is the problem the feature exists to solve.
"""

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
