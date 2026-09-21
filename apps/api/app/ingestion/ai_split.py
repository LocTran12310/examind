"""AI stage of the pipeline (US-05): re-split low-confidence blocks, AI-only mode, vision OCR.

Models come from the registry and the document's processing config; each call tries the
configured models in order and falls back to the rule result when none answers (AC-19).
"""
import io

import structlog

from app.ingestion import llm, ocr
from app.ingestion.lines import Line
from app.ingestion.pipeline import POST_SPLIT
from app.ingestion.splitter import ParsedQuestion, _finalise
from app.services.ai_models import resolve_for_org

log = structlog.get_logger("ai_split")
AI_CONFIDENCE_CAP = 0.9
NO_AI = "AI không phản hồi"

SPLIT_SYSTEM = """Bạn là trợ lý số hóa đề thi Việt Nam. Nhận nội dung MỘT câu hỏi (Markdown, công thức LaTeX giữa $...$,
ảnh dạng ![](asset:...)) và trả về DUY NHẤT một JSON:
{"type": "mcq|true_false|short_answer|essay", "stem": "...", "options": [{"label": "A", "content": "...", "is_true": null}],
 "answer": "C" | {"a": true, "b": false, "c": true, "d": true} | "giá trị" | null, "solution": "..." | null}
Quy tắc: giữ nguyên công thức và thẻ ảnh; mcq có 4 phương án A-D; true_false có 4 mệnh đề a-d;
short_answer không có options; không bịa đáp án — nếu đề không cho đáp án thì answer = null."""

MULTI_SYSTEM = SPLIT_SYSTEM.replace("MỘT câu hỏi", "một đoạn đề gồm NHIỀU câu").replace(
    "trả về DUY NHẤT một JSON:\n", 'trả về DUY NHẤT JSON {"questions": [ ... ]}, mỗi phần tử có thêm "number", dạng:\n')

VISION_SYSTEM = """Chép lại CHÍNH XÁC nội dung trang đề thi trong ảnh, giữ thứ tự đọc, mỗi dòng một dòng.
Công thức toán viết LaTeX giữa $...$. Không giải, không bình luận."""


def _models(ctx, ids: list[str], need: str = "text"):
    out = []
    for mid in ids:
        m = resolve_for_org(ctx.db, ctx.doc.organization_id, mid)
        if m and need in (m.capabilities or []):
            out.append(m)
    return out


def _call_chain(models, system: str, user: str, ctx, images=None, json_mode=True):
    errors = []
    for m in models:
        try:
            r = llm.chat(m, system, user, images=images, json_mode=json_mode)
            return m, (llm.parse_json(r.text) if json_mode else r.text)
        except llm.LlmError as exc:
            errors.append(f"{m.name}: {exc}")
            log.warning("ai.model_failed", model=m.model, error=str(exc))
    if errors:
        ctx.warnings.append("; ".join(errors)[:300])
    return None, None


def _from_json(data: dict, base: ParsedQuestion) -> ParsedQuestion | None:
    qtype = data.get("type")
    if qtype not in ("mcq", "true_false", "short_answer", "essay"):
        return None
    q = ParsedQuestion(number=base.number, part=base.part, type=qtype, raw=base.raw, pages=base.pages, ocr=base.ocr)
    q.stem = str(data.get("stem") or "").strip()
    q.solution = str(data.get("solution") or "").strip()
    opts = data.get("options") or []
    if qtype == "mcq":
        q.options = [{"label": str(o.get("label", "")).strip(" .)").upper(), "content": str(o.get("content", "")).strip()} for o in opts if isinstance(o, dict)]
        ans = data.get("answer")
        if isinstance(ans, str) and ans.strip(" .").upper() in {o["label"] for o in q.options}:
            q.answer, q.answer_source = {"key": ans.strip(" .").upper()}, "llm"
    elif qtype == "true_false":
        q.options = [{"label": str(o.get("label", "")).strip(" .)").lower(), "content": str(o.get("content", "")).strip(),
                      "is_true": o.get("is_true") if isinstance(o.get("is_true"), bool) else None} for o in opts if isinstance(o, dict)]
        ans = data.get("answer")
        if isinstance(ans, dict):
            for o in q.options:
                if isinstance(ans.get(o["label"]), bool):
                    o["is_true"] = ans[o["label"]]
        if q.options and all(o["is_true"] is not None for o in q.options):
            q.answer, q.answer_source = {o["label"]: o["is_true"] for o in q.options}, "llm"
    elif qtype == "short_answer":
        ans = data.get("answer")
        if ans not in (None, ""):
            q.answer, q.answer_source = {"value": str(ans)}, "llm"
    if not q.stem:
        return None
    _finalise(q)
    q.confidence = min(q.confidence, AI_CONFIDENCE_CAP)
    q.parse_method = "llm"  # type: ignore[attr-defined]
    return q


def ai_stage(db, doc, questions: list[ParsedQuestion], ctx) -> None:
    cfg = doc.processing_config or {}
    mode = cfg.get("split_mode", "rule")
    if mode == "rule":
        return
    models = _models(ctx, cfg.get("split_models") or [])
    if not models:
        ctx.warnings.append("Chế độ AI được chọn nhưng chưa có model khả dụng — dùng kết quả quy tắc")
        return
    if not questions and getattr(ctx, "lines", None):
        questions.extend(_split_whole(models, ctx))
        ctx.step("ai_split_whole", questions=len(questions))
        return
    threshold = cfg.get("threshold", 0.85)
    targets = [i for i, q in enumerate(questions) if mode == "ai" or q.confidence < threshold]
    replaced = failed = 0
    for i in targets:
        base = questions[i]
        user = f"Câu {base.number}.\n{base.raw}"
        model, data = _call_chain(models, SPLIT_SYSTEM, user, ctx)
        new = _from_json(data, base) if data else None
        if new is None:
            if model is None:
                base.issues.append(NO_AI)
                failed += 1
            continue
        new.parse_model = model.model  # type: ignore[attr-defined]
        questions[i] = new
        replaced += 1
    ctx.step("ai_split", candidates=len(targets), replaced=replaced, failed=failed)


def _split_whole(models, ctx, chunk_chars: int = 6000) -> list[ParsedQuestion]:
    """Rules found nothing: let the model segment the whole text, chunk by chunk."""
    chunks, cur = [], ""
    for line in ctx.lines:
        if len(cur) + len(line.text) > chunk_chars and cur:
            chunks.append(cur)
            cur = ""
        cur += line.text + "\n"
    if cur:
        chunks.append(cur)
    out: list[ParsedQuestion] = []
    for chunk in chunks:
        model, data = _call_chain(models, MULTI_SYSTEM, chunk, ctx)
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


def vision_provider(ctx):
    cfg = ctx.doc.processing_config or {}
    ids = [cfg["vision_model"]] if cfg.get("vision_model") else []
    models = _models(ctx, ids, need="vision")
    if not models:
        ctx.warnings.append("Model AI đọc ảnh không khả dụng — dùng Tesseract")
        return ocr.tesseract_page

    def page(image, pno):
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="PNG")
        model, text = _call_chain(models, VISION_SYSTEM, f"Trang {pno}.", ctx, images=[buf.getvalue()], json_mode=False)
        if text is None:
            return ocr.tesseract_page(image, pno)
        return [Line(t.strip(), pno, ocr=True, confidence=0.8) for t in text.splitlines() if t.strip()]

    return page


POST_SPLIT.append(ai_stage)
ocr.PROVIDERS["vision"] = vision_provider
