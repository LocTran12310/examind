import json
import os
import re

from cryptography.fernet import Fernet
import httpx
import pytest
from sqlalchemy import select

from app.modules.ingestion.infrastructure.adapters import llm
from app.modules.taxonomy.domain.topics import Topic
from app.shared.infrastructure.config import get_settings
from tests.test_documents_api import EXAMS, run_jobs, sample, teacher_with_taxonomy, upload


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_encryption_key", Fernet.generate_key().decode())


def test_keyword_suggestions_match_the_golden_topics(client, db):
    t = teacher_with_taxonomy(client, db)
    doc_id = upload(client, "de.docx", sample("de-mau-toan10.docx")).json()["document"]["id"]
    run_jobs()
    truth = {q["number"]: q["topic"] for q in json.load(open(os.path.join(EXAMS, "de-mau-toan10.expected.json"), encoding="utf-8"))["questions"]}
    topics = {x.name: x for x in db.scalars(select(Topic).where(Topic.organization_id == t.organization_id))}
    qs = client.get(f"/api/documents/{doc_id}/questions").json()
    good = 0
    for q in qs:
        assert len([x for x in q["topics"] if x["is_primary"]]) <= 1
        if not q["topics"]:
            continue
        got = topics[q["topics"][0]["name"]]
        want = topics[truth[q["number"]]]
        good += got.path == want.path or got.path.startswith(want.path + ".")
        assert q["topics"][0]["source"] == "auto" and 0 < q["topics"][0]["score"] <= 0.95
    assert good / len(qs) >= 0.9, f"{good}/{len(qs)}"


def test_ai_tagger_fills_questions_without_keyword_cues(client, db, monkeypatch):
    def handler(request):
        body = json.loads(request.content)
        user = body["messages"][-1]["content"]
        listing = user.split("CÂU HỎI:")[0]
        if "CHUYÊN ĐỀ:" not in listing:
            return _no_difficulty()
        idx = next(int(line.split(".")[0]) for line in listing.splitlines() if line.endswith("› Xác suất cổ điển"))
        numbers = _numbers(user.split("CÂU HỎI:")[1])
        return httpx.Response(200, json={"message": {"content": json.dumps({"results": [{"number": n, "index": idx, "confidence": 0.66} for n in numbers]})}})

    monkeypatch.setattr(llm, "TRANSPORT", httpx.MockTransport(handler))
    t = teacher_with_taxonomy(client, db)
    t.role = "org_admin"
    db.commit()
    mid = client.post("/api/ai-models", json={"name": "tag", "provider": "ollama", "model": "tag:1", "base_url": "http://t"}).json()["id"]
    doc_id = upload(client, "k.docx", sample("de-kho.docx"), config={"tag_model": mid}).json()["document"]["id"]
    run_jobs()
    qs = client.get(f"/api/documents/{doc_id}/questions").json()
    assert all(q["topics"][0]["name"] == "Xác suất cổ điển" and q["topics"][0]["source"] == "ai" and q["topics"][0]["score"] == 0.66 for q in qs)


def _tagger_answering(topic_name: str, with_name: str | None = None, shift: int = 0, asked: list | None = None):
    def handler(request):
        user = json.loads(request.content)["messages"][-1]["content"]
        listing, questions = user.split("CÂU HỎI:")
        if "CHUYÊN ĐỀ:" not in listing:
            return _no_difficulty()  # the same model is asked for mức độ too; this test is about the topics
        idx = next(int(line.split(".")[0]) for line in listing.splitlines() if line.endswith("› " + topic_name)) + shift
        numbers = _numbers(questions)
        if asked is not None:
            asked.extend(numbers)
        res = [{"number": n, "index": idx, "confidence": 0.9, **({"name": with_name} if with_name else {})} for n in numbers]
        return httpx.Response(200, json={"message": {"content": json.dumps({"results": res})}})
    return handler


def _numbers(questions: str) -> list[int]:
    return [int(m.group(1)) for m in re.finditer(r"^Câu (\d+):", questions, re.M)]


def _no_difficulty():
    """An empty answer to the difficulty request: the position rule keeps every question (difficulty-at-upload)."""
    return httpx.Response(200, json={"message": {"content": json.dumps({"results": []})}})


def _tag_model(client, db):
    t = teacher_with_taxonomy(client, db)
    t.role = "org_admin"
    db.commit()
    return client.post("/api/ai-models", json={"name": "tag", "provider": "ollama", "model": "tag:1", "base_url": "http://t"}).json()["id"]


def test_ai_tagger_never_overrides_strong_keywords(client, db, monkeypatch):
    """Golden run 2026-09-22: qwen2.5:7b put 'A ∩ B' (Q26) under 'Đại số tổ hợp' over a 0.73 keyword match."""
    asked: list = []
    monkeypatch.setattr(llm, "TRANSPORT", httpx.MockTransport(_tagger_answering("Đại số tổ hợp", asked=asked)))
    mid = _tag_model(client, db)
    doc_id = upload(client, "de.docx", sample("de-mau-toan10.docx"), config={"tag_model": mid}).json()["document"]["id"]
    run_jobs()
    qs = client.get(f"/api/documents/{doc_id}/questions").json()
    strong = [q for q in qs if q["topics"] and q["topics"][0]["source"] == "auto"]
    assert len(strong) >= 36 and all(q["number"] not in asked for q in strong)
    q26 = next(q for q in qs if q["number"] == 26)
    assert q26["topics"][0]["name"] == "Tập hợp và các phép toán" and q26["topics"][0]["source"] == "auto"


def test_ai_tagger_trusts_the_name_over_a_miscounted_index(client, db, monkeypatch):
    monkeypatch.setattr(llm, "TRANSPORT", httpx.MockTransport(_tagger_answering("Xác suất cổ điển", with_name="Xác suất cổ điển", shift=1)))
    mid = _tag_model(client, db)
    doc_id = upload(client, "k.docx", sample("de-kho.docx"), config={"tag_model": mid}).json()["document"]["id"]
    run_jobs()
    qs = client.get(f"/api/documents/{doc_id}/questions").json()
    assert all(q["topics"][0]["name"] == "Xác suất cổ điển" and q["topics"][0]["source"] == "ai" for q in qs)


def test_ai_tagger_drops_an_unknown_name(client, db, monkeypatch):
    monkeypatch.setattr(llm, "TRANSPORT", httpx.MockTransport(_tagger_answering("Xác suất cổ điển", with_name="Chuyên đề không có")))
    mid = _tag_model(client, db)
    doc_id = upload(client, "k.docx", sample("de-kho.docx"), config={"tag_model": mid}).json()["document"]["id"]
    run_jobs()
    qs = client.get(f"/api/documents/{doc_id}/questions").json()
    assert not any(q["topics"] and q["topics"][0]["source"] == "ai" for q in qs)


def test_ai_may_only_refine_a_weak_keyword_topic(client, db):
    from app.modules.ingestion.domain.services.topic_rules import _may_replace

    t = teacher_with_taxonomy(client, db)
    by = {x.name: x for x in db.scalars(select(Topic).where(Topic.organization_id == t.organization_id))}
    sets, combi, count = by["Tập hợp và các phép toán"], by["Đại số tổ hợp"], by["Hoán vị, chỉnh hợp, tổ hợp"]
    assert _may_replace(None, combi)
    assert _may_replace(combi, count)          # refine to a child
    assert not _may_replace(count, combi)      # never back up to the parent
    assert not _may_replace(sets, combi)       # never jump branches


def test_unicode_set_symbols_are_cues(client, db):
    from app.modules.ingestion.domain.services.topic_rules import keyword_scores

    t = teacher_with_taxonomy(client, db)
    topics = db.scalars(select(Topic).where(Topic.organization_id == t.organization_id)).all()
    weight, top = keyword_scores("Cho tập hợp A = 1; 2; 7 và B = 2; 7; 12. Tập A ∩ B là", topics)[0]
    assert top.name == "Tập hợp và các phép toán" and weight / (weight + 1) >= 0.6, (top.name, top.path, weight)
