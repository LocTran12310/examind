import json
import os

import httpx
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select

from app.core.config import get_settings
from app.ingestion import llm
from app.models import Topic
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


def test_ai_tagger_overrides_keywords(client, db, monkeypatch):
    def handler(request):
        body = json.loads(request.content)
        user = body["messages"][-1]["content"]
        listing = user.split("CÂU HỎI:")[0]
        idx = next(int(line.split(".")[0]) for line in listing.splitlines() if line.endswith("› Xác suất cổ điển"))
        numbers = [int(x.split(":")[0].replace("Câu ", "")) for x in user.split("CÂU HỎI:")[1].strip().split("\n\n")]
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
