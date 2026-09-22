import json
import os

from app.modules.ingestion.domain.services.splitter import split
from app.modules.ingestion.infrastructure.adapters.pdf import extract_pdf

EXAMS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "samples", "exams")


def load(name):
    with open(os.path.join(EXAMS, name), "rb") as fh:
        return fh.read()


def store_counter():
    pages = []

    def store(data, page=None):
        pages.append(page)
        return f"00000000-0000-0000-0000-{len(pages):012d}"

    return store, pages


def score(name, lines):
    truth = json.load(open(os.path.join(EXAMS, f"{name}.expected.json"), encoding="utf-8"))["questions"]
    got = {(q.part, q.number): q for q in split(lines).questions}
    ok = sum(1 for t in truth if (q := got.get((t["part"], t["number"]))) and q.answer == t["answer"] and len(q.options) == t["n_options"])
    return ok, len(truth), got


def test_text_pdf_reading_order_and_figures():
    store, pages = store_counter()
    warnings = []
    lines, n_pages = extract_pdf(load("de-mau-toan10.pdf"), store, warnings)
    assert n_pages >= 3 and not warnings
    assert len(pages) == 3 and all(p is not None for p in pages)
    ok, total, got = score("de-mau-toan10", lines)
    assert ok / total >= 0.95, f"{ok}/{total}"
    assert "asset:" in got[(None, 5)].options[2]["content"]


def test_two_column_pdf():
    store, _ = store_counter()
    lines, _ = extract_pdf(load("de-2cot.pdf"), store, [])
    ok, total, _ = score("de-2cot", lines)
    assert ok == total, f"{ok}/{total}"


def test_scanned_page_without_ocr_warns():
    warnings = []
    lines, n = extract_pdf(load("de-scan.pdf"), store_counter()[0], warnings)
    assert lines == [] and n == 2 and len(warnings) == 2


def test_combining_arrow_becomes_latex():
    from app.modules.ingestion.infrastructure.adapters.pdf import _normalise

    assert _normalise("vectơ pháp tuyến n⃗ = (1; 1) và AB⃗") == "vectơ pháp tuyến $\\vec{n}$ = (1; 1) và $\\vec{AB}$"
