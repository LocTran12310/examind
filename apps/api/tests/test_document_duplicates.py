"""Uploading a file that is already there: check, skip, re-parse, replace, keep both (critical: no silent duplicates)."""
import hashlib
import unicodedata

from sqlalchemy import func, select

from app.modules.ingestion.domain.entities import SourceDocument
from tests.test_documents_api import run_jobs, sample, teacher_with_taxonomy


def up(client, name, data, **form):
    return client.post("/api/documents", files={"file": (name, data, "application/octet-stream")}, data={"meta": "{}", "config": "{}", **form})


def count(db):
    db.expire_all()
    return db.scalar(select(func.count()).select_from(SourceDocument))


def test_same_content_is_never_stored_twice(client, db):
    teacher_with_taxonomy(client, db)
    data = sample("de-mau-toan10.docx")
    first = up(client, "de.docx", data)
    assert first.status_code == 201 and first.json()["action"] == "created"
    run_jobs()
    again = up(client, "ban-sao.docx", data)
    assert again.status_code == 200 and again.json()["action"] == "skipped" and again.json()["document"]["id"] == first.json()["document"]["id"]
    re = up(client, "de.docx", data, on_duplicate="replace")
    assert re.json()["action"] == "reparsed" and re.json()["document"]["status"] == "queued"
    assert count(db) == 1


def test_check_reports_same_file_and_same_name_in_any_unicode_form(client, db):
    teacher_with_taxonomy(client, db)
    data = sample("de-mau-toan10.docx")
    name = "Đề thi thử Ninh Bình.docx"
    doc = up(client, unicodedata.normalize("NFD", name), data).json()["document"]
    r = client.post("/api/documents/check", json={"files": [
        {"name": name, "sha256": hashlib.sha256(data).hexdigest()},
        {"name": name.upper(), "sha256": "0" * 64},
        {"name": "khac.docx", "sha256": "1" * 64},
    ]}).json()
    assert r[0]["same_file"]["id"] == doc["id"] and r[0]["same_name"] == []
    assert r[1]["same_file"] is None and [d["id"] for d in r[1]["same_name"]] == [doc["id"]]
    assert r[2]["same_file"] is None and r[2]["same_name"] == []


def test_replace_swaps_the_file_of_the_chosen_document(client, db):
    teacher_with_taxonomy(client, db)
    old = up(client, "de.docx", sample("de-mau-toan10.docx")).json()["document"]
    run_jobs()
    new_data = sample("de-thpt2025-toan.docx")
    r = up(client, "de.docx", new_data, on_duplicate="replace", replace_id=old["id"])
    assert r.status_code == 200 and r.json()["action"] == "replaced" and r.json()["document"]["id"] == old["id"]
    run_jobs()
    d = client.get(f"/api/documents/{old['id']}").json()
    assert d["status"] == "parsed" and d["question_count"] == 22 and count(db) == 1
    assert len(client.get(f"/api/documents/{old['id']}/questions").json()) == 22
    both = up(client, "de.docx", sample("de-kho.docx"), on_duplicate="keep_both")
    assert both.json()["action"] == "created" and count(db) == 2
    assert up(client, "x.docx", sample("de-kho.docx"), on_duplicate="bogus").status_code == 422


def test_deleting_the_original_releases_its_duplicates(client, db):
    from app.modules.bank.domain.entities import Question

    teacher_with_taxonomy(client, db)
    first = up(client, "de.docx", sample("de-mau-toan10.docx")).json()["document"]["id"]
    run_jobs()
    second = up(client, "de.pdf", sample("de-mau-toan10.pdf")).json()["document"]["id"]
    run_jobs()
    db.expire_all()
    dup = db.scalar(select(func.count()).select_from(Question).where(Question.source_document_id == second, Question.status == "duplicate"))
    assert dup > 0  # the PDF repeats the Word file's questions
    assert client.delete(f"/api/documents/{first}").status_code == 204
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(Question).where(Question.source_document_id == second, Question.status == "duplicate")) == 0
    assert db.scalar(select(func.count()).select_from(Question).where(Question.source_document_id == second, Question.status == "needs_review")) >= dup
