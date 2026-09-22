"""One set of quality rules for parsed and edited questions (question-review ADR-02, A-02). Shared by ingestion (parse time)
and the bank (edits, review): the published language of a question's quality."""
import re

from app.shared.domain.text import strip_markup

# Issues that stop auto-approval and manual approval alike.
BLOCKING = frozenset({
    "thiếu đề bài", "thiếu phương án", "thừa phương án", "phương án trống", "phương án có thể bị dính vào đề",
    "đáp án không có trong phương án", "không đủ 4 mệnh đề", "thiếu đáp án", "thiếu đáp án một số mệnh đề",
    "đáp án không khớp bảng đáp án", "đáp án không khớp định dạng", "nhiều phương án được đánh dấu",
    "không nhận ra phương án", "AI không phản hồi", "OCR", "Nghi sai đáp án",
})
# Issues only a parser can raise; a teacher's edit clears them.
PARSE_ONLY = frozenset({"đáp án không khớp bảng đáp án", "đáp án không khớp định dạng", "nhiều phương án được đánh dấu",
                        "không nhận ra phương án", "AI không phản hồi", "OCR"})
KEEP_ON_EDIT = frozenset({"Nghi sai đáp án"})  # only an explicit approval settles it


def evaluate(qtype: str, stem: str, options: list[dict], answer: dict | None, solution: str, *,
             extra_issues: list[str] = (), ocr: bool = False) -> tuple[list[str], float]:
    score = 1.0
    issues = list(extra_issues)
    if not (stem or "").strip():
        score -= 0.5
        issues.append("thiếu đề bài")
    if qtype == "mcq":
        n = len(options)
        if n < 4:
            score -= 0.4
            issues.append("thiếu phương án")
        elif n > 4:
            score -= 0.3
            issues.append("thừa phương án")
        if any(not (o.get("content") or "").strip() for o in options):
            score -= 0.2
            issues.append("phương án trống")
        if re.search(r"(?:^|\s)[B-D]\.\s", strip_markup(stem or "")):
            score -= 0.2
            issues.append("phương án có thể bị dính vào đề")
        if answer and answer.get("key") not in {o.get("label") for o in options}:
            score -= 0.3
            issues.append("đáp án không có trong phương án")
    if qtype == "true_false":
        if len(options) != 4:
            score -= 0.3
            issues.append("không đủ 4 mệnh đề")
        if answer is not None and any(v is None for v in answer.values()):
            score -= 0.1
            issues.append("thiếu đáp án một số mệnh đề")
    if "không nhận ra phương án" in issues:
        score -= 0.4
    if not answer and qtype != "essay":
        score -= 0.2
        issues.append("thiếu đáp án")
    if not (solution or "").strip():
        issues.append("thiếu lời giải")  # informational: no penalty
    if "đáp án không khớp bảng đáp án" in issues or "đáp án không khớp định dạng" in issues:
        score -= 0.2
    if ocr:
        score = min(score, 0.8)
        issues.append("OCR")
    seen: set[str] = set()
    issues = [i for i in issues if not (i in seen or seen.add(i))]
    return issues, round(max(0.0, min(1.0, score)), 2)


# Flags that only ask for a human look: a teacher's approval settles them.
NEEDS_EYES = frozenset({"OCR", "AI không phản hồi", "đáp án không khớp bảng đáp án", "đáp án không khớp định dạng",
                        "nhiều phương án được đánh dấu", "phương án có thể bị dính vào đề", "Nghi sai đáp án"})


def blocking(issues: list[str]) -> list[str]:
    """Issues that stop auto-approval."""
    return [i for i in issues or [] if i in BLOCKING]


def blocking_manual(issues: list[str]) -> list[str]:
    """Issues a teacher must fix before approving (structural problems)."""
    return [i for i in issues or [] if i in BLOCKING and i not in NEEDS_EYES]


def settle(q) -> None:
    """A teacher approved the question: flags that only asked for a look are resolved."""
    q.issues = [i for i in q.issues or [] if i not in NEEDS_EYES]


def triage_status(confidence: float | None, issues: list[str], threshold: float) -> str:
    return "auto_approved" if (confidence or 0) >= threshold and not blocking(issues) else "needs_review"


def reevaluate(q) -> None:
    """After a human edit: parse-only flags are dropped, the rest recomputed."""
    keep = [i for i in (q.issues or []) if i in KEEP_ON_EDIT or (i not in PARSE_ONLY and i not in BLOCKING and i != "thiếu lời giải")]
    q.issues, q.confidence = evaluate(q.type, q.stem, q.options or [], q.answer, q.solution, extra_issues=keep)
