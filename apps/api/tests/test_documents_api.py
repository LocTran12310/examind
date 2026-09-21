import os

from sqlalchemy import select

from app.core import db as dbmod
from app.models import Job, Question, SourceDocument, Subject
from app.worker import queue
from tests.factories import login_as

EXAMS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "samples", "exams")


def sample(name):
    with open(os.path.join(EXAMS, name), "rb") as fh:
        return fh.read()


def upload(client, name, data, meta=None, config=None):
    import json

    return client.post("/api/documents", files={"file": (name, data, "application/octet-stream")},
                       data={"meta": json.dumps(meta or {}), "config": json.dumps(config or {})})


def run_jobs():
    import app.ingestion.jobs  # noqa: F401
    while queue.run_one(dbmod.session_factory(), "test"):
        pass


def teacher_with_taxonomy(client, db):
    t = login_as(client, db, "teacher")
    from app.seed.org_template import seed_org

    seed_org(db, t.organization_id)
    db.commit()
    return t


def test_upload_parse_and_list(client, db):
    t = teacher_with_taxonomy(client, db)
    math = db.scalar(select(Subject).where(Subject.organization_id == t.organization_id, Subject.code == "toan"))
    meta = {"subject_id": str(math.id), "grade": 10, "semester_code": "hk1", "exam_kind": "Giữa kỳ", "source_name": "THPT Chu Văn An"}
    r = upload(client, "de-mau-toan10.docx", sample("de-mau-toan10.docx"), meta)
    assert r.status_code == 201, r.text
    doc = r.json()["document"]
    assert doc["status"] == "queued" and doc["processing_config"]["split_mode"] == "rule"
    assert db.scalar(select(Job).where(Job.kind == "ingest_document")) is not None
    run_jobs()
    d = client.get(f"/api/documents/{doc['id']}").json()
    assert d["status"] == "parsed" and d["question_count"] == 40, d
    assert [s["step"] for s in d["log"]][:4] == ["download", "extract", "split", "persist"]
    qs = client.get(f"/api/documents/{doc['id']}/questions").json()
    assert len(qs) == 40
    q1 = qs[0]
    assert q1["number"] == 1 and q1["grade"] == 10 and q1["semester_code"] == "hk1" and q1["exam_kind"] == "Giữa kỳ"
    assert q1["subject_id"] == str(math.id) and q1["status"] == "draft"
    assert [t["name"] for t in q1["tags"]] == ["THPT Chu Văn An"]
    assert client.get("/api/documents").json()["total"] == 1
    got = client.get(f"/api/documents/{doc['id']}/file")
    assert got.status_code == 200 and got.content == sample("de-mau-toan10.docx")


def test_duplicate_returns_existing(client, db):
    teacher_with_taxonomy(client, db)
    first = upload(client, "a.docx", sample("de-kho.docx")).json()["document"]["id"]
    r = upload(client, "b.docx", sample("de-kho.docx"))
    assert r.status_code == 200 and r.json()["duplicate"] is True and r.json()["document"]["id"] == first


def test_validation(client, db):
    teacher_with_taxonomy(client, db)
    ole = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"0" * 100
    r = upload(client, "old.doc", ole)
    assert r.status_code == 422 and ".docx" in r.json()["error"]["message"]
    r = upload(client, "x.exe", b"MZ" + b"0" * 100)
    assert r.status_code == 422 and r.json()["error"]["code"] == "unsupported_file"
    r = upload(client, "x.docx", sample("de-kho.docx"), {"grade": 13})
    assert r.status_code == 422 and "grade" in r.json()["error"]["fields"]


def test_reparse_keeps_approved_and_replaces_drafts(client, db):
    teacher_with_taxonomy(client, db)
    doc_id = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    run_jobs()
    q = db.scalar(select(Question).where(Question.number == 6))
    q.status, q.stem = "approved", "Đã sửa tay"
    db.commit()
    before = {x.id for x in db.scalars(select(Question))}
    assert client.post(f"/api/documents/{doc_id}/reparse", json={}).status_code == 202
    run_jobs()
    db.expire_all()
    rows = db.scalars(select(Question).where(Question.source_document_id == doc_id)).all()
    assert len(rows) == 8
    assert db.get(Question, q.id).stem == "Đã sửa tay"
    assert len(before & {x.id for x in rows}) == 1  # only the approved one survived


def test_failed_parse_is_reported(client, db):
    teacher_with_taxonomy(client, db)
    broken = b"PK\x03\x04" + b"not really a zip" * 10
    doc_id = upload(client, "broken.docx", broken).json()["document"]["id"]
    run_jobs()
    d = client.get(f"/api/documents/{doc_id}").json()
    assert d["status"] == "failed" and "Không đọc được file Word" in d["error"]
    assert "Traceback" not in d["error"]


def test_isolation(client, db):
    teacher_with_taxonomy(client, db)
    doc_id = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    other = client.__class__(client.app)
    from tests.factories import make_org, make_user

    org = make_org(db, "orgb")
    make_user(db, org, "gvb", role="teacher")
    db.commit()
    other.post("/api/auth/login", json={"org_code": "orgb", "username": "gvb", "password": "Secret123!"})
    assert other.get(f"/api/documents/{doc_id}").status_code == 404
    assert other.get(f"/api/documents/{doc_id}/questions").status_code == 404
    assert db.scalar(select(SourceDocument).where(SourceDocument.id == doc_id)) is not None
