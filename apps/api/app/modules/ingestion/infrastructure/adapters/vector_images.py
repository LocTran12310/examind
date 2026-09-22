"""WMF/EMF pictures → trimmed PNG (official-exam-ingestion ADR-03).

Official exam files draw figures (hình chóp, đồ thị, bảng biến thiên) and formula previews as
Windows metafiles, which browsers cannot show. LibreOffice renders them to PDF; pypdfium2 turns the
page into pixels and Pillow cuts the white margins. Everything is optional: without `soffice`, or
when a file fails, `to_png` returns None and the caller keeps its old "unsupported picture" path.
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile

import structlog

log = structlog.get_logger("ingest")

TIMEOUT = 30
SCALE = 2.0  # 144 dpi — sharp on screen without huge files
MARGIN = 4


def kind(data: bytes) -> str | None:
    """'wmf' | 'emf' | None from magic bytes."""
    if data[:4] == b"\xd7\xcd\xc6\x9a" or data[:6] in (b"\x01\x00\x09\x00\x00\x03", b"\x02\x00\x09\x00\x00\x03"):
        return "wmf"
    if len(data) >= 44 and data[:4] == b"\x01\x00\x00\x00" and data[40:44] == b" EMF":
        return "emf"
    return None


def soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def to_png(data: bytes) -> bytes | None:
    """PNG bytes, b"" for a blank drawing, None when it cannot be converted."""
    ext = kind(data)
    exe = soffice()
    if ext is None or exe is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, f"in.{ext}")
        with open(src, "wb") as fh:
            fh.write(data)
        try:
            proc = subprocess.run(
                # a private profile per call: concurrent workers must not share LibreOffice's lock
                [exe, f"-env:UserInstallation=file://{tmp}/profile", "--headless", "--norestore",
                 "--convert-to", "pdf", "--outdir", tmp, src],
                capture_output=True, timeout=TIMEOUT, check=False,
            )
        except subprocess.TimeoutExpired:
            log.warning("vector_image.timeout", kind=ext)
            return None
        pdf = os.path.join(tmp, "in.pdf")
        if proc.returncode != 0 or not os.path.exists(pdf):
            log.warning("vector_image.failed", kind=ext, stderr=proc.stderr.decode(errors="replace")[:200])
            return None
        with open(pdf, "rb") as fh:
            return _render(fh.read())


def _render(pdf: bytes) -> bytes | None:  # b"" = nothing drawn
    from PIL import Image, ImageChops
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf)
    try:
        if len(doc) == 0:
            return None
        image = doc[0].render(scale=SCALE).to_pil().convert("RGB")
    finally:
        doc.close()
    box = ImageChops.difference(image, Image.new("RGB", image.size, "white")).getbbox()
    if box is None:
        return b""  # blank drawing (e.g. the preview of an empty formula)
    left, top, right, bottom = box
    image = image.crop((max(0, left - MARGIN), max(0, top - MARGIN), min(image.width, right + MARGIN), min(image.height, bottom + MARGIN)))
    out = io.BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


class LibreOfficeVectorImages:
    """VectorImages port (module functions looked up at call time: tests switch LibreOffice off)."""

    def kind(self, data: bytes) -> str | None:
        return kind(data)

    def to_png(self, data: bytes) -> bytes | None:
        return to_png(data)
