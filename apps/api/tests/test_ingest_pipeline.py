"""The difficulty pass of the pipeline, end to end (difficulty-at-upload US-01).

A paper goes in, and every question comes out with a mức độ — that is the whole point: 376 of 378 questions in the
bank had none, so every blueprint row that asked for one came back empty. The model improves the levels where it
answers; it is never what the coverage depends on.
"""
from collections import Counter
import json
import re

from cryptography.fernet import Fernet
import httpx
import pytest

from app.modules.ingestion.infrastructure.adapters import llm
from app.shared.infrastructure.config import get_settings
from tests.test_documents_api import run_jobs, sample, teacher_with_taxonomy, upload


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_encryption_key", Fernet.generate_key().decode())


def _model(client, db):
    """The org's classification model: the topic pass and the difficulty pass both use it."""
    t = teacher_with_taxonomy(client, db)
    t.role = "org_admin"
    db.commit()
    return client.post("/api/ai-models", json={"name": "q", "provider": "ollama", "model": "q:1", "base_url": "http://q"}).json()["id"]


def _questions(client, name="de-mau-toan10.docx", config=None):
    doc_id = upload(client, name, sample(name), config=config).json()["document"]["id"]
    run_jobs()
    doc = client.get(f"/api/documents/{doc_id}").json()
    return doc, client.get(f"/api/documents/{doc_id}/questions").json()


def _answering(levels: dict, on_topics=None, only_first_batch: bool = False):
    """A model that answers the difficulty request for the numbers in `levels`; a topic request is answered
    separately (it names the tree) so one registered model can serve both passes.

    The numbers are the prompt's, and the prompt numbers each batch from one (T-02-04) — so `{1: …}` means "the
    first question of every batch" unless `only_first_batch` narrows it to one call. Before that fix the caller
    passed the paper's own numbers, which is exactly the confusion that let two questions share a number.
    """
    calls = []

    def handler(request):
        user = json.loads(request.content)["messages"][-1]["content"]
        if "CHUYÊN ĐỀ:" in user:
            return httpx.Response(200, json={"message": {"content": json.dumps({"results": on_topics or []})}})
        calls.append(user)
        numbers = [int(m.group(1)) for m in re.finditer(r"^Câu (\d+):", user.split("CÂU HỎI:")[1], re.M)]
        answer = levels if not only_first_batch or len(calls) == 1 else {}
        results = [{"number": n, "level": answer[n]} for n in numbers if n in answer]
        return httpx.Response(200, json={"message": {"content": json.dumps({"results": results})}})
    return handler


def test_no_question_leaves_the_pipeline_without_a_level(client, db):
    """AC-01: with no model configured at all, the position rule covers the paper end to end."""
    teacher_with_taxonomy(client, db)
    doc, qs = _questions(client)
    assert len(qs) == 40 and all(q["difficulty"] for q in qs)
    assert {q["difficulty_source"] for q in qs} == {"auto"}
    assert [s["step"] for s in doc["log"]][-1] == "suggest_difficulty"
    assert doc["log"][-1] == {"step": "suggest_difficulty", "ms": doc["log"][-1]["ms"], "rule": 40, "ai": 0}
    # a paper with no PHẦN header is read easy-first over its whole length
    by_number = {q["number"]: q["difficulty"] for q in qs}
    assert (by_number[1], by_number[15], by_number[16], by_number[30], by_number[31], by_number[38]) == \
           ("nb", "nb", "th", "th", "vd", "vdc")


def test_the_parts_of_a_thpt_paper_each_get_their_own_band(client, db):
    """AC-01 on the layout the rule is written for: PHẦN I trắc nghiệm, PHẦN II đúng/sai, PHẦN III trả lời ngắn."""
    teacher_with_taxonomy(client, db)
    _, qs = _questions(client, "de-thpt2025-toan.docx")
    levels = {(q["part"], q["number"]): q["difficulty"] for q in qs}
    assert len(qs) == 22 and all(q["difficulty_source"] == "auto" for q in qs)
    assert Counter(levels.values()) == {"vd": 7, "nb": 6, "th": 6, "vdc": 3}
    assert (levels[("1", 1)], levels[("1", 12)]) == ("nb", "vd")
    assert (levels[("2", 1)], levels[("2", 4)]) == ("th", "vd")
    assert (levels[("3", 1)], levels[("3", 6)]) == ("vd", "vdc")


def test_the_model_leads_where_it_answers_and_the_rule_keeps_the_rest(client, db, monkeypatch):
    """AC-02: the model is the only signal that reads the question, so it wins where it replies — and the questions
    it skipped are filled by the rule rather than left empty."""
    monkeypatch.setattr(llm, "TRANSPORT",
                        httpx.MockTransport(_answering({1: "vdc", 2: "vd", 3: "không rõ"}, only_first_batch=True)))
    mid = _model(client, db)
    _, qs = _questions(client, config={"tag_model": mid})
    by_number = {q["number"]: q for q in qs}
    assert (by_number[1]["difficulty"], by_number[1]["difficulty_source"]) == ("vdc", "ai")
    assert (by_number[2]["difficulty"], by_number[2]["difficulty_source"]) == ("vd", "ai")
    # an answer outside the four levels is dropped, and câu 3 keeps the level its position implies
    assert (by_number[3]["difficulty"], by_number[3]["difficulty_source"]) == ("nb", "auto")
    assert all(q["difficulty"] for q in qs) and Counter(q["difficulty_source"] for q in qs) == {"auto": 38, "ai": 2}


def test_every_part_of_a_thpt_paper_gets_the_model_answer_meant_for_it(client, db, monkeypatch):
    """T-02-04, on the paper the bug needed. THPT numbering restarts at each phần, so this document holds a câu 1
    three times over; a batch spanning two of them used to ask about "câu 1" twice and keep one answer, and Phần II
    lost its level in all 18 of the owner's papers without a single warning.

    The model here answers every question it is asked, so anything still `auto` is an answer that was thrown away.
    """
    monkeypatch.setattr(llm, "TRANSPORT", httpx.MockTransport(_answering({n: "vdc" for n in range(1, 11)})))
    mid = _model(client, db)
    _, qs = _questions(client, "de-thpt2025-toan.docx", config={"tag_model": mid})

    by_part = Counter(q["part"] for q in qs if q["difficulty_source"] == "auto")
    assert by_part == {}, f"câu bị bỏ mất câu trả lời của model, theo phần: {dict(by_part)}"
    assert {q["difficulty_source"] for q in qs} == {"ai"} and len(qs) == 22


@pytest.mark.parametrize("reply", [httpx.Response(200, json={"message": {"content": "Câu 1 là nhận biết."}}),
                                   httpx.Response(500, text="model down")])
def test_a_model_that_fails_is_a_warning_not_a_failed_upload(client, db, monkeypatch, reply):
    """AC-03: missing, disabled, slow or rambling — the paper is still parsed, every question still has a level,
    and the teacher is told in the document's log."""
    monkeypatch.setattr(llm, "TRANSPORT", httpx.MockTransport(lambda request: reply))
    mid = _model(client, db)
    doc, qs = _questions(client, config={"tag_model": mid})
    assert doc["status"] == "parsed" and len(qs) == 40
    assert {q["difficulty_source"] for q in qs} == {"auto"} and all(q["difficulty"] for q in qs)
    warnings = next(s["items"] for s in doc["log"] if s["step"] == "warnings")
    assert any("Model đoán mức độ lỗi" in w for w in warnings)


def test_a_level_a_teacher_set_survives_a_re_parse(client, db):
    """AC-04: a question the teacher approved and graded keeps its mức độ and its trace when the paper is parsed
    again — the machine passes never reach a level a person set (ADR-04)."""
    teacher_with_taxonomy(client, db)
    doc_id = upload(client, "de.docx", sample("de-mau-toan10.docx")).json()["document"]["id"]
    run_jobs()
    qid = client.get(f"/api/documents/{doc_id}/questions").json()[0]["id"]
    assert client.post(f"/api/review/questions/{qid}/action", json={"action": "approve"}).status_code == 200
    graded = client.patch(f"/api/questions/{qid}", json={"difficulty": "vdc"}).json()
    assert (graded["difficulty"], graded["difficulty_source"]) == ("vdc", "manual")
    assert client.post(f"/api/documents/{doc_id}/reparse", json={}).status_code == 202
    run_jobs()
    again = client.get(f"/api/questions/{qid}").json()
    assert (again["difficulty"], again["difficulty_source"]) == ("vdc", "manual")
