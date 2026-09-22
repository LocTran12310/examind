"""Tesseract OCR (exam-ingestion ADR-05): `vie` by default; AI vision is the ai_split stage's alternative."""
import io
import subprocess
import tempfile

from PIL import Image, ImageOps

from app.modules.ingestion.domain.errors import OcrError
from app.modules.ingestion.domain.services.lines import Line
from app.modules.ingestion.domain.services.ocr_text import parse_tsv

TESSERACT_TIMEOUT = 180
MIN_WORD_CONF = 0  # keep everything; confidence is reported per line


def tesseract_page(image: Image.Image, page: int, lang: str = "vie") -> list[Line]:
    img = ImageOps.grayscale(image)
    if img.width < 1600:  # small photos: upscale for better recognition
        ratio = 1600 / img.width
        img = img.resize((1600, int(img.height * ratio)))
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        img.save(tmp.name)
        try:
            proc = subprocess.run(["tesseract", tmp.name, "stdout", "-l", lang, "--psm", "4", "tsv"],
                                  capture_output=True, timeout=TESSERACT_TIMEOUT, check=False)
        except subprocess.TimeoutExpired as exc:
            raise OcrError("OCR quá thời gian") from exc
    if proc.returncode != 0:
        raise OcrError("OCR thất bại: " + proc.stderr.decode(errors="replace")[:200])
    return parse_tsv(proc.stdout.decode("utf-8", errors="replace"), page)


class TesseractScanner:
    """Scanner port: Pillow decodes and encodes, Tesseract reads."""

    def open(self, data: bytes) -> Image.Image:
        image = Image.open(io.BytesIO(data))
        image.load()
        return image

    def tesseract(self, image, page: int) -> list[Line]:
        return tesseract_page(image, page)

    def png(self, image) -> bytes:
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="PNG")
        return buf.getvalue()
