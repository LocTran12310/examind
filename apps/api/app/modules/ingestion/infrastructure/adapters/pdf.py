"""PDF → line stream (exam-ingestion ADR-04): pdfplumber for words in reading order, pypdfium2 for crops.

Two-column pages are detected by a clear gutter around the middle; full-width rows (titles, tables)
break the page into segments so each segment is read left column then right column.
Pages without a text layer are handed to the OCR callback.
"""
import io
import re

import pdfplumber
import pypdfium2 as pdfium

from app.modules.ingestion.domain.ports import ImageStore, OcrPage
from app.modules.ingestion.domain.services.lines import Line

RENDER_SCALE = 2.0      # crops at 144 dpi
MIN_TEXT_CHARS = 20     # fewer characters than this → treat the page as scanned
ROW_TOLERANCE = 3.0


def extract_pdf(data: bytes, store: ImageStore, warnings: list[str], ocr_page: OcrPage | None = None) -> tuple[list[Line], int]:
    lines: list[Line] = []
    doc = pdfium.PdfDocument(data)
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for pno, page in enumerate(pdf.pages, start=1):
                if len(page.chars) < MIN_TEXT_CHARS:
                    if ocr_page is None:
                        warnings.append(f"Trang {pno} là ảnh scan nhưng chưa bật OCR")
                        continue
                    image = doc[pno - 1].render(scale=300 / 72).to_pil()
                    lines += ocr_page(image, pno)
                    continue
                lines += _text_page(page, doc[pno - 1], pno, store)
            return lines, len(pdf.pages)
    finally:
        doc.close()


def _rows(words: list[dict]) -> list[list[dict]]:
    rows: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if rows and abs(rows[-1][0]["top"] - w["top"]) <= ROW_TOLERANCE:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w["x0"]) for r in rows]


_COMBINING_ARROW = re.compile(r"([A-Za-z]{1,2})\u20d7")


def _normalise(text: str) -> str:
    """PDF text keeps Word's combining arrow (n⃗, AB⃗) which most fonts cannot draw: write it as LaTeX."""
    return _COMBINING_ARROW.sub(lambda m: f"$\\vec{{{m.group(1)}}}$", text)


def _row_text(row: list[dict]) -> str:
    parts = []
    for i, w in enumerate(row):
        text = w["text"]
        if "Bold" in (w.get("fontname") or "") and len(text) <= 2 and text[:1] in "ABCD" and text.endswith((".", ")")):
            text = f"**{text}**"
        parts.append(text)
    return _normalise(" ".join(parts))


def _is_two_column(rows: list[list[dict]], mid: float) -> bool:
    left = right = 0
    for r in rows:
        if any(w["x0"] < mid < w["x1"] for w in r):
            continue
        left += any(w["x1"] <= mid for w in r)
        right += any(w["x0"] >= mid for w in r)
    return left >= 3 and right >= 3


def _text_page(page, pdfium_page, pno: int, store: ImageStore) -> list[Line]:
    words = page.extract_words(extra_attrs=["fontname", "size"], x_tolerance=1.5, keep_blank_chars=False)
    mid = page.width / 2
    rows = _rows(words)
    images = [im for im in page.images if (im["x1"] - im["x0"]) > 15 and (im["bottom"] - im["top"]) > 15]
    rendered = None
    items: list[tuple[str, float, float, str]] = []  # (column, top, x0, text)
    two_col = _is_two_column(rows, mid)
    for r in rows:
        crosses = any(w["x0"] < mid < w["x1"] for w in r)
        if not two_col or crosses:
            items.append(("full", r[0]["top"], r[0]["x0"], _row_text(r)))
            continue
        left = [w for w in r if w["x1"] <= mid]
        right = [w for w in r if w["x0"] >= mid]
        if left:
            items.append(("L", left[0]["top"], left[0]["x0"], _row_text(left)))
        if right:
            items.append(("R", right[0]["top"], right[0]["x0"], _row_text(right)))
    for im in images:
        if rendered is None:
            rendered = pdfium_page.render(scale=RENDER_SCALE).to_pil()
        box = tuple(int(v * RENDER_SCALE) for v in (im["x0"], im["top"], im["x1"], im["bottom"]))
        buf = io.BytesIO()
        rendered.crop(box).convert("RGB").save(buf, format="PNG")
        asset_id = store(buf.getvalue(), pno)
        if asset_id:
            col = "full" if not two_col or im["x0"] < mid < im["x1"] else ("L" if im["x1"] <= mid else "R")
            items.append((col, im["top"], im["x0"], f"![](asset:{asset_id})"))
    return [Line(text, pno) for text in _reading_order(items)]


def _reading_order(items: list[tuple[str, float, float, str]]) -> list[str]:
    """Full-width rows split the page into bands; inside a band read the left column, then the right."""
    out: list[str] = []
    band: list[tuple[str, float, float, str]] = []

    def flush():
        for col in ("L", "R"):
            out.extend(t for c, _, _, t in sorted((i for i in band if i[0] == col), key=lambda i: (i[1], i[2])))
        band.clear()

    for item in sorted(items, key=lambda i: (i[1], i[2])):
        if item[0] == "full":
            flush()
            out.append(item[3])
        else:
            band.append(item)
    flush()
    return out


class PdfplumberReader:
    """PdfReader port."""

    def read(self, data: bytes, store: ImageStore, warnings: list[str], ocr_page: OcrPage | None = None) -> tuple[list[Line], int]:
        return extract_pdf(data, store, warnings, ocr_page)


class PdfiumPageRenderer:
    """PageRenderer port: a PDF page at 108 dpi for the review queue."""

    def render_png(self, pdf: bytes, page: int) -> bytes:
        doc = pdfium.PdfDocument(pdf)
        try:
            img = doc[page - 1].render(scale=1.5).to_pil()
        finally:
            doc.close()
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG", optimize=True)
        return buf.getvalue()
