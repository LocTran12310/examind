"""MathType objects in .docx become $…$ before Pandoc (official-exam-ingestion AC-01, AC-02)."""
import io
import zipfile
from pathlib import Path

from app.modules.ingestion.domain.services.docx_ast import inline_mathtype
from app.modules.ingestion.infrastructure.adapters.pandoc import extract_docx

FIX = Path(__file__).parent / "fixtures" / "mtef"
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"'


def _object(n: int) -> str:
    return (f'<w:object w:dxaOrig="480" w:dyaOrig="400"><v:shape id="s{n}" style="width:20pt;height:20pt" o:ole="">'
            f'<v:imagedata r:id="rImg{n}" o:title=""/></v:shape>'
            f'<o:OLEObject Type="Embed" ProgID="Equation.DSMT4" ShapeID="s{n}" DrawAspect="Content" ObjectID="_{n}" r:id="rOle{n}"/></w:object>')


def make_docx(oles: list[bytes], body: str) -> bytes:
    """`body` is paragraph XML where `{EQn}` marks the n-th equation run."""
    for n in range(len(oles)):
        body = body.replace(f"{{EQ{n}}}", f"<w:r>{_object(n)}</w:r>")
    rels = "".join(
        f'<Relationship Id="rImg{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image{n}.wmf"/>'
        f'<Relationship Id="rOle{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject" Target="embeddings/oleObject{n}.bin"/>'
        for n in range(len(oles)))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/><Default Extension="wmf" ContentType="image/x-wmf"/>'
                   '<Default Extension="bin" ContentType="application/vnd.openxmlformats-officedocument.oleObject"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/document.xml", f'<?xml version="1.0"?><w:document {W}><w:body>{body}</w:body></w:document>')
        z.writestr("word/_rels/document.xml.rels", f'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>')
        for n, ole in enumerate(oles):
            z.writestr(f"word/embeddings/oleObject{n}.bin", ole)
            z.writestr(f"word/media/image{n}.wmf", b"\xd7\xcd\xc6\x9a" + b"\x00" * 40)
    return out.getvalue()


def para(xml: str) -> str:
    return f"<w:p>{xml}</w:p>"


def run(text: str, bold: bool = False, mark: bool = False) -> str:
    props = ("<w:b/>" if bold else "") + ('<w:highlight w:val="yellow"/>' if mark else "")
    return f'<w:r><w:rPr>{props}</w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>'


def store_spy():
    stored = []

    def store(data, page=None):
        stored.append(data)
        return f"00000000-0000-0000-0000-{len(stored):012d}"

    return store, stored


def test_equations_become_latex_and_no_picture_is_stored():
    frac, log = (FIX / "frac.bin").read_bytes(), (FIX / "log.bin").read_bytes()
    doc = make_docx([frac, log], para(run("Câu 1: ", bold=True) + run("Tính ") + "{EQ0}" + run(" biết ") + "{EQ1}" + run(".")))
    store, stored = store_spy()
    lines, warnings = extract_docx(doc, store)
    assert lines[0].text == r"**Câu 1:** Tính $\frac{a}{b}$ biết $y=\log_{2}x$."
    assert stored == [] and warnings == []


def test_highlight_around_an_equation_is_kept():
    """Official keys highlight the whole correct option, formula included: [**D.** $…$]{.mark}."""
    marked_eq = f'<w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr>{_object(0)}</w:r>'
    doc = make_docx([(FIX / "frac.bin").read_bytes()], para(run("D. ", bold=True, mark=True) + marked_eq))
    lines, _ = extract_docx(doc, store_spy()[0])
    assert "\\frac{a}{b}" in lines[0].text and lines[0].text.startswith("[") and lines[0].text.endswith("]{.mark}")


def test_unconvertible_equation_keeps_its_picture_with_a_warning():
    doc = make_docx([b"garbage"], para(run("Câu 2: ") + "{EQ0}"))
    data, math, failed = inline_mathtype(doc)
    assert (math, failed) == ({}, 1)
    store, stored = store_spy()
    lines, warnings = extract_docx(doc, store)
    assert any("1 công thức MathType" in w for w in warnings)
    assert "asset:" in "\n".join(l.text for l in lines) or any("hình" in w for w in warnings)


def test_documents_without_equations_are_untouched():
    doc = make_docx([], para(run("Câu 3: không có công thức")))
    assert inline_mathtype(doc) == (doc, {}, 0)
