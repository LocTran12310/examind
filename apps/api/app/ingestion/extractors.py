"""Registers the PDF and image extractors with the pipeline (UOW-02)."""
import io

from PIL import Image

from app.ingestion import ocr
from app.ingestion.pdf import extract_pdf
from app.ingestion.pipeline import EXTRACTORS, IngestError


def _ocr_page_fn(ctx):
    engine = (ctx.doc.processing_config or {}).get("ocr", "auto")
    name = "vision" if engine == "vision" and "vision" in ocr.PROVIDERS else "tesseract"
    if engine == "vision" and name != "vision":
        ctx.warnings.append("Chưa cấu hình model AI đọc ảnh — dùng Tesseract")
    fn = ocr.PROVIDERS[name](ctx)

    def page(image, pno):
        try:
            return fn(image, pno)
        except ocr.OcrError as exc:
            raise IngestError(str(exc)) from exc

    return page


def pdf_extractor(db, doc, data, store, ctx):
    try:
        lines, pages = extract_pdf(data, store, ctx.warnings, _ocr_page_fn(ctx))
    except IngestError:
        raise
    except Exception as exc:  # malformed PDFs raise many different errors
        raise IngestError("Không đọc được file PDF") from exc
    doc.page_count = pages
    return lines


def image_extractor(db, doc, data, store, ctx):
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:
        raise IngestError("Không đọc được ảnh") from exc
    doc.page_count = 1
    return _ocr_page_fn(ctx)(image, 1)


EXTRACTORS["pdf"] = pdf_extractor
EXTRACTORS["image"] = image_extractor
