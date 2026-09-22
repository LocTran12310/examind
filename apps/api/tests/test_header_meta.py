"""Header metadata suggestions and editing a document's meta (official-exam-ingestion AC-09)."""
from types import SimpleNamespace

from sqlalchemy import select

from app.modules.bank.domain.entities import Question
from app.modules.ingestion.domain.services.header import apply, detect
from app.modules.ingestion.domain.services.lines import Line
from app.modules.ingestion.infrastructure.adapters.taxonomy import SqlTaxonomyLookup
from app.modules.taxonomy.domain.entities import Subject
from tests.test_documents_api import run_jobs, sample, teacher_with_taxonomy, upload

NGUYEN_KHUYEN = """**SỞ GD&ĐT TP. HCM**
**TRƯỜNG THCS -THPT NGUYỄN KHUYẾN**
**ĐỀ THI THI THỬ TỐT NGHIỆP LẦN 1**
**NĂM HỌC: 2024 - 2025**
**MÔN: TOÁN**
(Thời gian làm bài: 90 phút, không kể thời gian giao đề)
**PHẦN I: CÂU TRẮC NGHIỆM NHIỀU PHƯƠNG ÁN LỰA CHỌN**
**Câu 1:** Cho cấp số cộng … Sở dĩ LẦN 9 không được đọc""".split("\n")


def test_detect_official_headers():
    assert detect(NGUYEN_KHUYEN) == {
        "province": "TP HCM", "issuer": "Trường THCS-THPT Nguyễn Khuyến", "school_year": "2024-2025",
        "subject_name": "Toán", "grade": 12, "exam_kind": "Thi thử", "attempt": 1, "duration": 90,
    }
    yen_bai = detect(["**SỞ GIÁO DỤC VÀ ĐÀO TẠO**", "**YÊN BÁI**", "**ĐỀ THI THI THỬ TỐT NGHIỆP LẦN 1**", "**MÔN: TOÁN**"])
    assert yen_bai["issuer"] == "Sở GD&ĐT Yên Bái"
    thach_thanh = detect(["SỞ GD&ĐT THANH HOÁ", "TRƯỜNG THPT THẠCH THÀNH I", "**ĐỀ THI KHẢO SÁT CHẤT LƯỢNG LẦN 1**",
                          "**NĂM HỌC 2024 – 2025**", "**Môn: TOÁN, Lớp 12**", "Thời gian: 90 phút"])
    assert thach_thanh["exam_kind"] == "Khảo sát" and thach_thanh["grade"] == 12 and thach_thanh["subject_name"] == "Toán"
    le_thanh_tong = detect(["**ĐỀ THI THỬ TỐT NGHIỆP THPT NĂM 2025**", "**Bài thi: TOÁN**"])
    assert le_thanh_tong["school_year"] == "2024-2025" and le_thanh_tong["exam_kind"] == "Thi thử"
    assert detect(["**Câu 1.** Không có tiêu đề"]) == {}


def test_apply_fills_only_empty_fields(client, db):
    t = teacher_with_taxonomy(client, db)
    math = db.scalar(select(Subject).where(Subject.organization_id == t.organization_id, Subject.code == "toan"))
    doc = SimpleNamespace(organization_id=t.organization_id, meta={"exam_kind": "Ôn tập"})
    apply(doc, [Line(x) for x in NGUYEN_KHUYEN], SqlTaxonomyLookup(db).subjects(t.organization_id))
    assert doc.meta["subject_id"] == str(math.id) and doc.meta["grade"] == 12
    assert doc.meta["exam_kind"] == "Ôn tập"  # the uploader's choice wins
    assert doc.meta["source_name"] == "Trường THCS-THPT Nguyễn Khuyến" and doc.meta["school_year"] == "2024-2025"
    assert doc.meta["detected"]["attempt"] == 1


def test_patch_meta_updates_the_questions(client, db):
    t = teacher_with_taxonomy(client, db)
    math = db.scalar(select(Subject).where(Subject.organization_id == t.organization_id, Subject.code == "toan"))
    doc = upload(client, "de-mau-toan10.docx", sample("de-mau-toan10.docx"), {"source_name": "Nguồn cũ"}).json()["document"]
    run_jobs()
    r = client.patch(f"/api/documents/{doc['id']}", json={"meta": {"subject_id": str(math.id), "grade": 11, "exam_kind": "Thi thử", "source_name": "Sở GD&ĐT Ninh Bình"}})
    assert r.status_code == 200, r.text
    assert r.json()["meta"]["grade"] == 11
    qs = client.get(f"/api/documents/{doc['id']}/questions").json()
    assert {q["grade"] for q in qs} == {11} and {q["exam_kind"] for q in qs} == {"Thi thử"}
    assert all([tg["name"] for tg in q["tags"]] == ["Sở GD&ĐT Ninh Bình"] for q in qs)
    assert client.patch(f"/api/documents/{doc['id']}", json={"meta": {"grade": 13}}).status_code == 422
    db.expire_all()
    assert db.scalar(select(Question).where(Question.source_document_id == doc["id"])).subject_id == math.id
