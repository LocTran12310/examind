"""OCR providers (exam-ingestion ADR-05). Tesseract `vie` by default; AI vision is plugged in by ai_split."""
from collections.abc import Callable
import csv
import io
import subprocess
import tempfile

from PIL import Image, ImageOps

from app.ingestion.lines import Line

TESSERACT_TIMEOUT = 180
MIN_WORD_CONF = 0  # keep everything; confidence is reported per line

# name -> factory(ctx) -> OcrPage ; "vision" is registered by the AI stage
PROVIDERS: dict[str, Callable] = {}


class OcrError(Exception):
    pass


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


def parse_tsv(tsv: str, page: int) -> list[Line]:
    lines: dict[tuple, list[tuple[str, float]]] = {}
    order: list[tuple] = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row.get("level") != "5" or not (row.get("text") or "").strip():
            continue
        key = (row["block_num"], row["par_num"], row["line_num"])
        if key not in lines:
            lines[key] = []
            order.append(key)
        lines[key].append((row["text"], max(0.0, float(row["conf"] or 0))))
    out = []
    for key in order:
        words = lines[key]
        text = " ".join(w for w, _ in words).strip()
        conf = sum(c for _, c in words) / len(words) / 100
        out.append(Line(text, page, ocr=True, confidence=round(conf, 2)))
    return out


PROVIDERS["tesseract"] = lambda ctx: tesseract_page
