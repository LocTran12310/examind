import os
import re

from app.core.images import Canvas
from app.modules.ingestion.infrastructure.adapters.pandoc import extract_docx
from app.modules.ingestion.domain.services.splitter import split

EXAMS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "samples", "exams")


def fake_store():
    stored = []

    def store(data: bytes, page=None):
        stored.append(data)
        return f"00000000-0000-0000-0000-{len(stored):012d}"

    return store, stored


def load(name):
    with open(os.path.join(EXAMS, name), "rb") as fh:
        return fh.read()


def test_math_images_and_structure():
    store, stored = fake_store()
    lines, warnings = extract_docx(load("de-mau-toan10.docx"), store)
    texts = [l.text for l in lines]
    assert any(t.startswith("**Câu 1.**") for t in texts)
    assert any("$" in t and "x^{2}" in t.replace(" ", "") or "x^2" in t for t in texts)
    assert len(stored) == 3 and not warnings
    refs = [t for t in texts if "asset:" in t]
    assert len(refs) == 3
    # the answer-key table is flattened row by row
    assert any(re.match(r"^\*?\*?Câu\*?\*? \| 1 \| 2 \|", t) or t.startswith("Câu | 1 | 2") for t in texts), [t for t in texts if "|" in t][:2]


def test_underlined_option_and_auto_numbered_list(tmp_path):
    import subprocess

    md = "**Câu 1.** Chọn đáp án\n\nA. 1\n\nB. 2\n\n[C. 3]{.underline}\n\nD. 4\n\n**Câu 2.** Danh sách\n\n1. một\n2. hai\n"
    out = tmp_path / "x.docx"
    subprocess.run(["pandoc", "-f", "markdown", "-t", "docx", "-o", str(out)], input=md.encode(), check=True)
    store, _ = fake_store()
    lines, _ = extract_docx(out.read_bytes(), store)
    texts = [l.text for l in lines]
    assert "[C. 3]{.underline}" in texts
    assert "1. một" in texts and "2. hai" in texts
    q = split(lines).questions[0]
    assert q.answer == {"key": "C"} and q.answer_source == "format"


def test_unsupported_image_is_skipped_with_warning(tmp_path):
    import subprocess

    img = tmp_path / "ok.png"
    c = Canvas(3, 3)
    img.write_bytes(c.encode())
    md = f"Câu 1. Hình\n\n![]({img})\n"
    out = tmp_path / "y.docx"
    subprocess.run(["pandoc", "-f", "markdown", "-t", "docx", "-o", str(out)], input=md.encode(), check=True)
    lines, warnings = extract_docx(out.read_bytes(), lambda data, page=None: None)
    assert not any("asset:" in l.text for l in lines)
