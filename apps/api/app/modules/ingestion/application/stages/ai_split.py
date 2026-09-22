"""AI stage of the pipeline (US-05): re-split low-confidence blocks, AI-only mode, vision OCR.

Models come from the registry and the document's processing config; each call tries the
configured models in order and falls back to the rule result when none answers (AC-19).
"""
import structlog

from app.modules.ingestion.application.models import usable_model
from app.modules.ingestion.application.run import IngestRun
from app.modules.ingestion.domain.errors import LlmError
from app.modules.ingestion.domain.ports import AiModelRepository, ChatModels, OcrPage, Scanner
from app.modules.ingestion.domain.services.ai_parse import (
    MULTI_SYSTEM, NO_AI, QUESTION_SCHEMA, SPLIT_SYSTEM, VISION_SYSTEM, _from_json, parse_json,
)
from app.modules.ingestion.domain.services.lines import Line
from app.modules.ingestion.domain.services.splitter import ParsedQuestion

log = structlog.get_logger("ai_split")


class AiSplitter:
    def __init__(self, models: AiModelRepository, chat: ChatModels, scanner: Scanner):
        self.models, self.chat, self.scanner = models, chat, scanner

    def _models(self, run: IngestRun, ids: list[str], need: str = "text"):
        out = []
        for mid in ids:
            m = usable_model(self.models, run.doc.organization_id, mid)
            if m and need in (m.capabilities or []):
                out.append(m)
        return out

    def _call_chain(self, models, system: str, user: str, run: IngestRun, images=None, json_mode=True, schema=None):
        errors = []
        for m in models:
            try:
                r = self.chat.chat(m, system, user, images=images, json_mode=json_mode, schema=schema)
                return m, (parse_json(r.text) if json_mode else r.text)
            except LlmError as exc:
                errors.append(f"{m.name}: {exc}")
                log.warning("ai.model_failed", model=m.model, error=str(exc))
        if errors:
            run.warnings.append("; ".join(errors)[:300])
        return None, None

    def stage(self, questions: list[ParsedQuestion], run: IngestRun) -> None:
        """After the rule split: may rewrite `questions` in place."""
        cfg = run.doc.processing_config or {}
        mode = cfg.get("split_mode", "rule")
        if mode == "rule":
            return
        models = self._models(run, cfg.get("split_models") or [])
        if not models:
            run.warnings.append("Chế độ AI được chọn nhưng chưa có model khả dụng — dùng kết quả quy tắc")
            return
        if not questions and run.lines:
            questions.extend(self._split_whole(models, run))
            run.step("ai_split_whole", questions=len(questions))
            return
        threshold = cfg.get("threshold", 0.85)
        targets = [i for i, q in enumerate(questions) if mode == "ai" or q.confidence < threshold]
        replaced = failed = 0
        for i in targets:
            base = questions[i]
            user = f"Câu {base.number}.\n{base.raw}"
            model, data = self._call_chain(models, SPLIT_SYSTEM, user, run, schema=QUESTION_SCHEMA)
            new = _from_json(data, base) if data else None
            if new is None:
                if model is None:
                    base.issues.append(NO_AI)
                    failed += 1
                continue
            new.parse_model = model.model  # type: ignore[attr-defined]
            questions[i] = new
            replaced += 1
        run.step("ai_split", candidates=len(targets), replaced=replaced, failed=failed)

    def _split_whole(self, models, run: IngestRun, chunk_chars: int = 6000) -> list[ParsedQuestion]:
        """Rules found nothing: let the model segment the whole text, chunk by chunk."""
        chunks, cur = [], ""
        for line in run.lines:
            if len(cur) + len(line.text) > chunk_chars and cur:
                chunks.append(cur)
                cur = ""
            cur += line.text + "\n"
        if cur:
            chunks.append(cur)
        out: list[ParsedQuestion] = []
        for chunk in chunks:
            model, data = self._call_chain(models, MULTI_SYSTEM, chunk, run)
            for item in (data or {}).get("questions", []) if isinstance(data, dict) else []:
                if not isinstance(item, dict):
                    continue
                try:
                    number = int(item.get("number") or len(out) + 1)
                except (TypeError, ValueError):
                    number = len(out) + 1
                q = _from_json(item, ParsedQuestion(number=number, raw=chunk[:2000]))
                if q:
                    q.parse_model = model.model  # type: ignore[attr-defined]
                    out.append(q)
        return out

    def vision_page(self, run: IngestRun) -> OcrPage:
        """OCR by the document's vision model, Tesseract when none is usable or it does not answer."""
        cfg = run.doc.processing_config or {}
        ids = [cfg["vision_model"]] if cfg.get("vision_model") else []
        models = self._models(run, ids, need="vision")
        if not models:
            run.warnings.append("Model AI đọc ảnh không khả dụng — dùng Tesseract")
            return self.scanner.tesseract

        def page(image, pno):
            model, text = self._call_chain(models, VISION_SYSTEM, f"Trang {pno}.", run, images=[self.scanner.png(image)], json_mode=False)
            if text is None:
                return self.scanner.tesseract(image, pno)
            return [Line(t.strip(), pno, ocr=True, confidence=0.8) for t in text.splitlines() if t.strip()]

        return page
