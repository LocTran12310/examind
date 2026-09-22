"""Extraction stage: the file → the canonical line stream (exam-ingestion ADR-02, ADR-04, ADR-05).
Word through Pandoc, PDF through pdfplumber (scanned pages OCR'd), images OCR'd; the OCR engine is the
document's choice (Tesseract, or a vision model when one is usable)."""
from app.modules.ingestion.application.run import IngestRun
from app.modules.ingestion.application.stages.ai_split import AiSplitter
from app.modules.ingestion.domain.errors import DocxError, IngestError, OcrError
from app.modules.ingestion.domain.ports import DocxReader, ImageStore, OcrPage, PdfReader, Scanner
from app.modules.ingestion.domain.services.lines import Line


class Extractor:
    def __init__(self, docx: DocxReader, pdf: PdfReader, scanner: Scanner, ai: AiSplitter):
        self.docx, self.pdf, self.scanner, self.ai = docx, pdf, scanner, ai

    def __call__(self, data: bytes, store: ImageStore, run: IngestRun) -> list[Line]:
        doc = run.doc
        kind = doc.kind
        if kind == "docx":
            try:
                lines, warnings = self.docx.read(data, store, run.stats)
            except DocxError as exc:
                raise IngestError(str(exc)) from exc
            run.warnings += warnings
            return lines
        if kind == "pdf":
            return self._pdf(data, store, run)
        if kind == "image":
            return self._image(data, run)
        raise IngestError(f"Chưa hỗ trợ đọc loại file này ({kind})")

    def _ocr_page(self, run: IngestRun) -> OcrPage:
        engine = (run.doc.processing_config or {}).get("ocr", "auto")
        fn = self.ai.vision_page(run) if engine == "vision" else self.scanner.tesseract

        def page(image, pno):
            try:
                return fn(image, pno)
            except OcrError as exc:
                raise IngestError(str(exc)) from exc

        return page

    def _pdf(self, data: bytes, store: ImageStore, run: IngestRun) -> list[Line]:
        try:
            lines, pages = self.pdf.read(data, store, run.warnings, self._ocr_page(run))
        except IngestError:
            raise
        except Exception as exc:  # malformed PDFs raise many different errors
            raise IngestError("Không đọc được file PDF") from exc
        run.doc.page_count = pages
        return lines

    def _image(self, data: bytes, run: IngestRun) -> list[Line]:
        try:
            image = self.scanner.open(data)
        except Exception as exc:
            raise IngestError("Không đọc được ảnh") from exc
        run.doc.page_count = 1
        return self._ocr_page(run)(image, 1)
