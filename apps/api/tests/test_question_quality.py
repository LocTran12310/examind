from types import SimpleNamespace

from app.shared.domain.question_quality import blocking, evaluate, reevaluate, triage_status

OPTS = [{"label": l, "content": l.lower()} for l in "ABCD"]


def test_well_formed_mcq_scores_full():
    issues, conf = evaluate("mcq", "Đề", OPTS, {"key": "B"}, "Giải")
    assert issues == [] and conf == 1.0
    assert triage_status(conf, issues, 0.85) == "auto_approved"


def test_missing_answer_is_blocking_and_solution_is_not():
    issues, conf = evaluate("mcq", "Đề", OPTS, None, "")
    assert issues == ["thiếu đáp án", "thiếu lời giải"] and conf == 0.8
    assert blocking(issues) == ["thiếu đáp án"]
    assert triage_status(0.99, issues, 0.85) == "needs_review"


def test_ocr_caps_and_blocks():
    issues, conf = evaluate("mcq", "Đề", OPTS, {"key": "A"}, "g", ocr=True)
    assert conf == 0.8 and "OCR" in issues and triage_status(conf, issues, 0.5) == "needs_review"


def test_essay_needs_no_answer():
    issues, conf = evaluate("essay", "Chứng minh", [], None, "")
    assert conf == 1.0 and triage_status(conf, issues, 0.85) == "auto_approved"


def test_reevaluate_after_edit_drops_parse_only_flags():
    q = SimpleNamespace(type="mcq", stem="Đề", options=OPTS, answer={"key": "C"}, solution="x",
                        issues=["OCR", "thiếu đáp án", "đáp án không khớp bảng đáp án"], confidence=0.4)
    reevaluate(q)
    assert q.issues == [] and q.confidence == 1.0
