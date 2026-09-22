import json

import httpx
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select

from app.core.config import get_settings
from app.ingestion import llm
from app.models import Question
from tests.test_documents_api import run_jobs, sample, teacher_with_taxonomy, upload


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_encryption_key", Fernet.generate_key().decode())


def fake_model(monkeypatch, down=()):
    """Answer like a model: read the options out of 'Các lựa chọn: a; b; c; d.' and pick the second."""
    import re

    calls = []

    def handler(request: httpx.Request):
        host = request.url.host
        calls.append(host)
        if host in down:
            raise httpx.ConnectError("down")
        body = json.loads(request.content)
        user = body["messages"][-1]["content"]
        m = re.search(r"Câu (\d+)\.\n(.*?)Các lựa chọn: ([^.\n]+)", user, re.S)
        if not m:
            return httpx.Response(200, json={"message": {"content": "không hiểu"}})
        opts = [o.strip() for o in m.group(3).split(";")]
        data = {"type": "mcq", "stem": m.group(2).strip() + " ?", "options": [{"label": l, "content": o} for l, o in zip("ABCD", opts)],
                "answer": "B", "solution": None}
        return httpx.Response(200, json={"message": {"content": json.dumps(data, ensure_ascii=False)}})

    monkeypatch.setattr(llm, "TRANSPORT", httpx.MockTransport(handler))
    return calls


def add_model(client, name, host):
    return client.post("/api/ai-models", json={"name": name, "provider": "ollama", "model": f"{name}:7b", "base_url": f"http://{host}"}).json()["id"]


def test_rule_plus_ai_replaces_low_confidence_questions(client, db, monkeypatch):
    fake_model(monkeypatch)
    login = teacher_with_taxonomy(client, db)
    login.role = "org_admin"
    db.commit()
    mid = add_model(client, "qwen", "ai1")
    doc = upload(client, "k.docx", sample("de-kho.docx"), config={"split_mode": "rule_ai", "split_models": [mid]}).json()["document"]
    assert doc["processing_config"]["split_models"] == [mid]
    run_jobs()
    qs = {q["number"]: q for q in client.get(f"/api/documents/{doc['id']}/questions").json()}
    for n in range(1, 6):
        assert qs[n]["parse_method"] == "llm" and qs[n]["parse_model"] == "qwen:7b", qs[n]
        assert qs[n]["answer"] == {"key": "B"} and len(qs[n]["options"]) == 4
        assert qs[n]["confidence"] <= 0.9
    for n in range(6, 9):
        assert qs[n]["parse_method"] == "rule"


def test_chain_falls_back_then_reports_failure(client, db, monkeypatch):
    calls = fake_model(monkeypatch, down=("dead",))
    t = teacher_with_taxonomy(client, db)
    t.role = "org_admin"
    db.commit()
    dead, alive = add_model(client, "dead", "dead"), add_model(client, "alive", "ai2")
    doc = upload(client, "k.docx", sample("de-kho.docx"), config={"split_mode": "rule_ai", "split_models": [dead, alive]}).json()["document"]
    run_jobs()
    q1 = client.get(f"/api/documents/{doc['id']}/questions").json()[0]
    assert q1["parse_model"] == "alive:7b" and "dead" in calls
    # every model down → rule result kept with an issue
    fake_model(monkeypatch, down=("dead", "ai2"))
    client.post(f"/api/documents/{doc['id']}/reparse", json={"config": {"split_mode": "rule_ai", "split_models": [dead, alive]}})
    run_jobs()
    q1 = client.get(f"/api/documents/{doc['id']}/questions").json()[0]
    assert q1["parse_method"] == "rule" and "AI không phản hồi" in q1["issues"]


def test_reparse_switches_mode_and_records_config(client, db, monkeypatch):
    fake_model(monkeypatch)
    t = teacher_with_taxonomy(client, db)
    t.role = "org_admin"
    db.commit()
    mid = add_model(client, "qwen", "ai1")
    doc = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]
    run_jobs()
    assert all(q["parse_method"] == "rule" for q in client.get(f"/api/documents/{doc['id']}/questions").json())
    r = client.post(f"/api/documents/{doc['id']}/reparse", json={"config": {"split_mode": "rule_ai", "split_models": [mid]}})
    assert r.status_code == 202 and r.json()["processing_config"]["split_mode"] == "rule_ai"
    run_jobs()
    methods = [q["parse_method"] for q in client.get(f"/api/documents/{doc['id']}/questions").json()]
    assert methods.count("llm") == 5
    assert db.scalar(select(Question).where(Question.parse_method == "llm")) is not None


def test_model_from_other_org_is_ignored(client, db, monkeypatch):
    fake_model(monkeypatch)
    teacher_with_taxonomy(client, db)
    import uuid

    doc = upload(client, "k.docx", sample("de-kho.docx"), config={"split_mode": "rule_ai", "split_models": [str(uuid.uuid4())]}).json()["document"]
    run_jobs()
    d = client.get(f"/api/documents/{doc['id']}").json()
    warnings = next(l for l in d["log"] if l["step"] == "warnings")["items"]
    assert any("chưa có model khả dụng" in w for w in warnings)


def test_vision_ocr_engine(client, db, monkeypatch):
    seen = []

    def handler(request):
        body = json.loads(request.content)
        seen.append(len(body["messages"][1].get("images", [])))
        text = "Câu 1. Tọa độ đỉnh parabol là\nA. (1; 2)\nB. (2; 1)\nC. (0; 0)\nD. (3; 3)\nĐáp án: B"
        return httpx.Response(200, json={"message": {"content": text}})

    monkeypatch.setattr(llm, "TRANSPORT", httpx.MockTransport(handler))
    t = teacher_with_taxonomy(client, db)
    t.role = "org_admin"
    db.commit()
    vid = client.post("/api/ai-models", json={"name": "vl", "provider": "ollama", "model": "qwen2.5vl:7b", "base_url": "http://v",
                                              "capabilities": ["text", "vision"]}).json()["id"]
    doc = upload(client, "scan.png", sample("de-scan.png"), config={"ocr": "vision", "vision_model": vid}).json()["document"]
    run_jobs()
    qs = client.get(f"/api/documents/{doc['id']}/questions").json()
    assert seen == [1] and len(qs) == 1
    assert qs[0]["answer"] == {"key": "B"} and qs[0]["parse_method"] == "ocr" and "OCR" in qs[0]["issues"]


def test_normalises_small_model_drift():
    from app.ingestion.ai_split import _from_json
    from app.ingestion.splitter import ParsedQuestion

    raw = {"type": "multiple_choice", "stem": "Giá trị của $2^{1}$?", "answer": "2",
           "options": [{"label": "1", "content": "1"}, {"label": "2", "content": "2"}, {"label": "3", "content": "3"}, {"label": "4", "content": "4"}]}
    q = _from_json(raw, ParsedQuestion(number=1))
    assert q.type == "mcq" and [o["label"] for o in q.options] == list("ABCD") and q.answer == {"key": "B"}


def test_mcq_key_variants_from_7b_models():
    from app.ingestion.ai_split import _from_json
    from app.ingestion.splitter import ParsedQuestion

    opts = [{"label": l, "content": c, "is_true": l == "B"} for l, c in zip("ABCD", ["3", "4", "5", "8"])]
    for ans in ({"b": True}, {"key": "B"}, "Chọn B", "B. 4", "b", None):
        q = _from_json({"type": "mcq", "stem": "Giá trị của $2^2$?", "options": opts, "answer": ans}, ParsedQuestion(number=2))
        assert q.answer == {"key": "B"}, ans
    unmarked = [{**o, "is_true": None} for o in opts]
    q = _from_json({"type": "mcq", "stem": "x?", "options": unmarked, "answer": {"a": True, "b": True}}, ParsedQuestion(number=3))
    assert q.answer is None
