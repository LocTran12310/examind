"""Reading what a chat model answers (exam-ingestion ADR-03, US-05): JSON out of prose, the question schema and the
drift small local models show, turned back into a ParsedQuestion."""
import json
import re

from app.modules.ingestion.domain.errors import LlmError
from app.modules.ingestion.domain.services.splitter import ParsedQuestion, _finalise


def parse_json(text: str) -> dict:
    """Models wrap JSON in prose or code fences; take the outermost object."""
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end <= start:
        raise LlmError("Model không trả về JSON")
    try:
        value = json.loads(t[start:end + 1])
    except json.JSONDecodeError as exc:
        raise LlmError("JSON từ model không hợp lệ") from exc
    if not isinstance(value, dict):
        raise LlmError("JSON từ model không phải object")
    return value


AI_CONFIDENCE_CAP = 0.9
NO_AI = "AI không phản hồi"

SPLIT_SYSTEM = """Bạn là trợ lý số hóa đề thi Việt Nam. Nhận nội dung MỘT câu hỏi (Markdown, công thức LaTeX giữa $...$,
ảnh dạng ![](asset:...)) và trả về DUY NHẤT một JSON:
{"type": "mcq|true_false|short_answer|essay", "stem": "...", "options": [{"label": "A", "content": "...", "is_true": null}],
 "answer": "C" | {"a": true, "b": false, "c": true, "d": true} | "giá trị" | null, "solution": "..." | null}
Quy tắc: giữ nguyên công thức và thẻ ảnh; mcq có 4 phương án A-D; true_false có 4 mệnh đề a-d;
nếu đề liệt kê các lựa chọn (kể cả dạng "Các lựa chọn: 1; 2; 3; 4") thì type = mcq và gán nhãn A-D theo thứ tự;\nmcq: answer là MỘT chữ cái A-D (ví dụ "B"), không dùng object;\nshort_answer không có options; không bịa đáp án — nếu đề không cho đáp án thì answer = null."""  # noqa: E501

MULTI_SYSTEM = SPLIT_SYSTEM.replace("MỘT câu hỏi", "một đoạn đề gồm NHIỀU câu").replace(
    "trả về DUY NHẤT một JSON:\n", 'trả về DUY NHẤT JSON {"questions": [ ... ]}, mỗi phần tử có thêm "number", dạng:\n')

VISION_SYSTEM = """Chép lại CHÍNH XÁC nội dung trang đề thi trong ảnh, giữ thứ tự đọc, mỗi dòng một dòng.
Công thức toán viết LaTeX giữa $...$. Không giải, không bình luận."""


QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["mcq", "true_false", "short_answer", "essay"]},
        "stem": {"type": "string"},
        "options": {"type": "array", "items": {"type": "object", "properties": {
            "label": {"type": "string"}, "content": {"type": "string"}, "is_true": {"type": ["boolean", "null"]}},
            "required": ["label", "content"]}},
        "answer": {"type": ["string", "object", "null"]},
        "solution": {"type": ["string", "null"]},
    },
    "required": ["type", "stem", "options", "answer"],
}


TYPE_ALIASES = {"multiple_choice": "mcq", "multiple-choice": "mcq", "trac_nghiem": "mcq", "choice": "mcq",
                "true/false": "true_false", "truefalse": "true_false", "dung_sai": "true_false",
                "short": "short_answer", "fill": "short_answer", "open": "essay", "tu_luan": "essay"}


def _normalise(data: dict) -> dict:
    """Small local models drift from the schema: fix the common deviations before validating."""
    data = dict(data)
    t = str(data.get("type") or "").strip().lower()
    data["type"] = TYPE_ALIASES.get(t, t)
    opts = [o for o in (data.get("options") or []) if isinstance(o, dict)]
    if data["type"] == "mcq" and opts and not all(str(o.get("label", "")).strip(" .)").upper() in "ABCD" for o in opts):
        # labels given as 1..4 or as the option text: relabel in order, and map a numeric/text answer
        old = [str(o.get("label", "")).strip() for o in opts]
        ans = str(data.get("answer") or "").strip()
        for i, o in enumerate(opts[:4]):
            o["label"] = "ABCD"[i]
        if ans in old[:4]:
            data["answer"] = "ABCD"[old.index(ans)]
        elif ans in [str(o.get("content", "")).strip() for o in opts[:4]]:
            data["answer"] = "ABCD"[[str(o.get("content", "")).strip() for o in opts[:4]].index(ans)]
        data["options"] = opts[:4]
    if data["type"] == "mcq":
        data["answer"] = _mcq_key(data.get("answer"), opts)
    return data


_KEY_RE = re.compile(r"^(?:chọn|đáp án|answer)?\s*[:\-]?\s*([A-Da-d])\b", re.I)


def _mcq_key(ans, opts: list[dict]) -> str | None:
    """7B models mark the key as {"b": true}, {"key": "B"}, "Chọn B", "B. 4" or only via is_true."""
    labels = [str(o.get("label", "")).strip(" .)").upper() for o in opts]
    if isinstance(ans, dict):
        picked = [k for k, v in ans.items() if v is True]
        ans = picked[0] if len(picked) == 1 else ans.get("key") or ans.get("label") or ans.get("answer")
    if isinstance(ans, str) and (m := _KEY_RE.match(ans.strip())) and m.group(1).upper() in labels:
        return m.group(1).upper()
    marked = [labels[i] for i, o in enumerate(opts) if o.get("is_true") is True]
    return marked[0] if len(marked) == 1 else None


def _from_json(data: dict, base: ParsedQuestion) -> ParsedQuestion | None:
    data = _normalise(data)
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
