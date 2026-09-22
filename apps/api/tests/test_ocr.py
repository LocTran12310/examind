import json
import os

from PIL import Image

from app.modules.ingestion.infrastructure.adapters.tesseract import parse_tsv, tesseract_page
from app.modules.ingestion.domain.services.splitter import split
from tests.test_documents_api import EXAMS, run_jobs, sample, teacher_with_taxonomy, upload


def test_parse_tsv_groups_lines_with_confidence():
    tsv = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n" \
          "5\t1\t1\t1\t1\t1\t0\t0\t1\t1\t96\tCâu\n5\t1\t1\t1\t1\t2\t0\t0\t1\t1\t90\t1.\n" \
          "5\t1\t1\t1\t2\t1\t0\t0\t1\t1\t80\tA.\n5\t1\t1\t1\t2\t2\t0\t0\t1\t1\t-1\t \n"
    lines = parse_tsv(tsv, 3)
    assert [l.text for l in lines] == ["Câu 1.", "A."]
    assert lines[0].ocr and lines[0].page == 3 and lines[0].confidence == 0.93


def test_tesseract_reads_the_scanned_sample():
    lines = tesseract_page(Image.open(os.path.join(EXAMS, "de-scan.png")), 1)
    res = split(lines)
    expected = json.load(open(os.path.join(EXAMS, "de-scan.expected.json")))["png_numbers"]
    got = [q.number for q in res.questions]
    assert len(set(got) & set(expected)) >= len(expected) - 1, got
    assert all(q.ocr and q.confidence <= 0.8 and "OCR" in q.issues for q in res.questions)


def test_scanned_pdf_and_image_through_pipeline(client, db):
    teacher_with_taxonomy(client, db)
    for name, n_min in (("de-scan.pdf", 8), ("de-scan.png", 4)):
        doc_id = upload(client, name, sample(name)).json()["document"]["id"]
        run_jobs()
        d = client.get(f"/api/documents/{doc_id}").json()
        assert d["status"] == "parsed", d
        qs = client.get(f"/api/documents/{doc_id}/questions").json()
        assert len(qs) >= n_min, (name, len(qs))
        assert all(q["parse_method"] == "ocr" and q["confidence"] <= 0.8 for q in qs)


def test_text_pdf_through_pipeline(client, db):
    teacher_with_taxonomy(client, db)
    doc_id = upload(client, "de.pdf", sample("de-mau-toan10.pdf")).json()["document"]["id"]
    run_jobs()
    d = client.get(f"/api/documents/{doc_id}").json()
    assert d["status"] == "parsed" and d["question_count"] == 40 and d["page_count"] >= 3
