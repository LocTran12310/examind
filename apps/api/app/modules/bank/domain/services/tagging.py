"""Placing many questions in the topic tree at once, and keeping a question's subject and its topic in agreement
(pickers-builder ADR-02, A-04)."""
import uuid

from app.shared.domain.errors import Invalid

MAX_PAIRS = 200

# why a {question, topic} pair could not be applied; the queue shows these to the teacher
SKIP_REASONS = {
    "unknown_question": "Không tìm thấy câu hỏi",
    "other_org": "Câu hỏi của đơn vị khác",
    "unknown_topic": "Chuyên đề không hợp lệ",
    "no_subject": "Câu hỏi chưa có môn học",
    "subject_mismatch": "Chuyên đề không thuộc môn của câu hỏi",
}


def check_pairs(count: int) -> None:
    """A page of the tagging queue at a time: more than that is a client that forgot to page."""
    if count > MAX_PAIRS:
        raise Invalid(f"Tối đa {MAX_PAIRS} cặp câu hỏi – chuyên đề mỗi lần", "pairs")


def pair_skip(question_subject_id: uuid.UUID | None, topic_subject_id: uuid.UUID | None) -> str | None:
    """Why that topic cannot become that question's primary topic (None: it can). The topic's subject is None when
    the topic is unknown or belongs to another organisation — the bank does not tell those apart."""
    if topic_subject_id is None:
        return "unknown_topic"
    if question_subject_id is None:
        return "no_subject"
    if question_subject_id != topic_subject_id:
        return "subject_mismatch"
    return None


def check_subject_change(subject_id: uuid.UUID, placed: dict[uuid.UUID, tuple[uuid.UUID, uuid.UUID | None, str]]) -> None:
    """A bulk subject refuses to leave a question placed in another subject's tree: the teacher is told which
    questions and which topics stand in the way, and nothing is applied (A-04, decided by the owner 2026-09-23).
    `placed` is {question id: (topic id, the topic's subject, the topic's name)} for the questions that have a
    primary topic."""
    conflicts = [{"question_id": str(qid), "topic_id": str(tid), "topic_name": name}
                 for qid, (tid, topic_subject, name) in sorted(placed.items(), key=lambda kv: str(kv[0]))
                 if topic_subject is not None and topic_subject != subject_id]
    if not conflicts:
        return
    names = ", ".join(dict.fromkeys(c["topic_name"] for c in conflicts))
    message = (f"{len(conflicts)} câu đang có chuyên đề thuộc môn khác ({names}). "
               "Bỏ hoặc đổi chuyên đề của những câu đó trước khi đổi môn.")
    raise Invalid(message, code="subject_topic_conflict", fields={"subject_id": message, "conflicts": conflicts})
