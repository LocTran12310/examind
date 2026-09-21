"""Suggest a primary topic for each parsed question (US-06, A-13).

Keyword rules always run: every node of the org's tree contributes its own name plus curated
synonyms; the deepest, best-scoring node wins. When a tagging model is configured it chooses
among the same nodes and, when valid, overrides the keywords (source `ai`).
"""
import re
import unicodedata

from sqlalchemy import select, text

from app.ingestion import llm
from app.ingestion.pipeline import POST_PERSIST
from app.models import QuestionTopic, Subject, Topic
from app.services.ai_models import resolve_for_org

# Extra cues per seeded topic name (lower-case, accents kept). Names themselves are always cues.
SYNONYMS: dict[str, list[str]] = {
    "Hàm số bậc hai và đồ thị": ["parabol", "hàm số bậc hai", "y = x^2", "y = x^{2}", "trục đối xứng"],
    "Tìm đỉnh và trục đối xứng parabol": ["tọa độ đỉnh", "đỉnh của parabol", "trục đối xứng"],
    "Dấu của tam thức bậc hai": ["tam thức", "âm khi", "dương khi"],
    "Mệnh đề": ["mệnh đề", "phủ định", "\\forall", "\\exists"],
    "Tập hợp và các phép toán": ["tập hợp", "\\cap", "\\cup", "tập con", "giao của", "hợp của"],
    "Tích vô hướng của hai vectơ": ["tích vô hướng", "\\cdot \\vec", "vec{u} \\cdot"],
    "Các phép toán vectơ": ["tổng hai vectơ", "hiệu hai vectơ", "\\vec"],
    "Hệ thức lượng trong tam giác": ["tam giác", "diện tích tam giác", "định lý cosin", "định lí sin", "\\widehat"],
    "Hoán vị, chỉnh hợp, tổ hợp": ["số cách", "chỉnh hợp", "tổ hợp", "hoán vị", "c_{", "a_{"],
    "Quy tắc đếm": ["quy tắc cộng", "quy tắc nhân"],
    "Phương trình đường thẳng": ["đường thẳng", "vectơ pháp tuyến", "vectơ chỉ phương"],
    "Phương trình đường tròn": ["đường tròn", "tâm i", "bán kính"],
    "Nguyên hàm": ["nguyên hàm", "\\int f", "f(x)dx"],
    "Phương pháp đổi biến số": ["đổi biến", "đặt t ="],
    "Tích phân": ["tích phân", "\\int_"],
    "Ứng dụng tích phân tính diện tích": ["diện tích hình phẳng", "giới hạn bởi"],
    "Ứng dụng tích phân tính thể tích": ["thể tích khối tròn xoay", "quay quanh"],
    "Cực trị của hàm số": ["cực trị", "cực đại", "cực tiểu"],
    "Tính đơn điệu của hàm số": ["đồng biến", "nghịch biến"],
    "Giá trị lớn nhất, nhỏ nhất": ["giá trị lớn nhất", "giá trị nhỏ nhất"],
    "Đường tiệm cận": ["tiệm cận"],
    "Logarit": ["logarit", "\\log"],
    "Phương trình mũ và logarit": ["phương trình mũ", "phương trình logarit"],
    "Thể tích khối chóp": ["khối chóp", "hình chóp"],
    "Thể tích khối lăng trụ": ["lăng trụ"],
    "Phương trình mặt phẳng": ["mặt phẳng (p)", "phương trình mặt phẳng", "oxyz"],
    "Phương trình mặt cầu": ["mặt cầu"],
    "Xác suất cổ điển": ["xác suất", "biến cố"],
    "Phương trình lượng giác cơ bản": ["\\sin x =", "\\cos x =", "phương trình lượng giác"],
    "Dãy số, cấp số cộng, cấp số nhân": ["cấp số cộng", "cấp số nhân", "công sai", "công bội"],
    "Giới hạn và hàm số liên tục": ["giới hạn", "\\lim", "liên tục"],
    "Đạo hàm": ["đạo hàm", "f'(x)"],
}


def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").lower()


def _cues(topic: Topic) -> list[str]:
    name = _norm(topic.name)
    cues = [name] + [_norm(c) for c in SYNONYMS.get(topic.name, [])]
    return [c for c in cues if len(c) >= 3]


def keyword_scores(text: str, topics: list[Topic]) -> list[tuple[float, Topic]]:
    t = _norm(text)
    scored = []
    for topic in topics:
        hits = [c for c in _cues(topic) if c in t]
        if hits:
            weight = sum(1 + len(c) / 20 for c in hits) + topic.path.count(".") * 0.05  # prefer deeper nodes on ties
            scored.append((weight, topic))
    return sorted(scored, key=lambda x: -x[0])


def _candidates(db, doc) -> list[Topic]:
    subject_id = (doc.meta or {}).get("subject_id")
    stmt = select(Topic).where(Topic.organization_id == doc.organization_id)
    if subject_id:
        stmt = stmt.where(Topic.subject_id == subject_id)
    else:
        math = db.scalar(select(Subject.id).where(Subject.organization_id == doc.organization_id, Subject.code == "toan"))
        stmt = stmt.where(Topic.subject_id == math)
    return db.scalars(stmt.order_by(Topic.path)).all()


TAG_SYSTEM = """Bạn phân loại câu hỏi vào cây chuyên đề. Với mỗi câu, chọn MỘT chỉ số chuyên đề phù hợp nhất
(ưu tiên nhánh sâu nhất đúng). Trả về DUY NHẤT JSON {"results": [{"number": 1, "index": 12, "confidence": 0.8}]}."""


def _ai_choose(db, doc, rows, topics, ctx) -> dict:
    tag_model = (doc.processing_config or {}).get("tag_model")
    m = resolve_for_org(db, doc.organization_id, tag_model) if tag_model else None
    if m is None or not topics:
        return {}
    by_id = {t.id: t for t in topics}
    listing = "\n".join(f"{i}. {_label(t, by_id)}" for i, t in enumerate(topics))
    out: dict = {}
    for start in range(0, len(rows), 10):
        batch = rows[start:start + 10]
        qs = "\n\n".join(f"Câu {p.number}: {q.stem[:600]}" for p, q in batch)
        try:
            data = llm.parse_json(llm.chat(m, TAG_SYSTEM, f"CHUYÊN ĐỀ:\n{listing}\n\nCÂU HỎI:\n{qs}").text)
        except llm.LlmError as exc:
            ctx.warnings.append(f"Model gắn chuyên đề lỗi: {exc}")
            return out
        numbers = {p.number: q for p, q in batch}
        for r in data.get("results", []) if isinstance(data.get("results"), list) else []:
            try:
                q, idx = numbers[int(r["number"])], int(r["index"])
            except (KeyError, TypeError, ValueError):
                continue
            if 0 <= idx < len(topics):
                conf = r.get("confidence")
                out[q.id] = (topics[idx], float(conf) if isinstance(conf, (int, float)) else 0.7, m.model)
    return out


def _label(t: Topic, by_id: dict) -> str:
    names, cur = [], t
    while cur is not None:
        names.append(cur.name)
        cur = by_id.get(cur.parent_id)
    return " › ".join(reversed(names))


KNN_MIN_SIMILARITY = 0.35
WEAK_KEYWORD = 0.6


def knn_topic(db, q) -> tuple[Topic, float] | None:
    """A-08: the primary topic of the most similar teacher-approved question."""
    if not q.search_text:
        return None
    row = db.execute(text("""
        select qt.topic_id, similarity(o.search_text, :t) as s
          from questions o join question_topics qt on qt.question_id = o.id and qt.is_primary
         where o.organization_id = :org and o.status = 'approved' and o.id <> :id and o.search_text % :t
         order by s desc limit 1"""), {"t": q.search_text, "org": q.organization_id, "id": q.id}).first()
    if row is None or row[1] < KNN_MIN_SIMILARITY:
        return None
    return db.get(Topic, row[0]), round(float(row[1]), 2)


def suggest_topics(db, doc, rows, ctx) -> None:
    topics = _candidates(db, doc)
    if not topics or not rows:
        return
    ai = _ai_choose(db, doc, rows, topics, ctx)
    auto = with_ai = knn = 0
    for p, q in rows:
        if q.id in ai:
            topic, score, _ = ai[q.id]
            source = "ai"
            with_ai += 1
        else:
            scored = keyword_scores(q.stem + "\n" + " ".join(o.get("content", "") for o in q.options or []), topics)
            topic, score, source = None, 0.0, "auto"
            if scored:
                weight, topic = scored[0]
                score = round(min(0.95, weight / (weight + 1)), 2)
            if score < WEAK_KEYWORD:
                near = knn_topic(db, q)
                if near and near[1] >= score:
                    topic, score, source = near[0], near[1], "knn"
            if topic is None:
                continue
            if source == "knn":
                knn += 1
            else:
                auto += 1
        db.add(QuestionTopic(question_id=q.id, topic_id=topic.id, is_primary=True, source=source, score=round(score, 2)))
    db.flush()
    ctx.step("suggest_topics", keyword=auto, ai=with_ai, knn=knn, none=len(rows) - auto - with_ai - knn)


POST_PERSIST.append(suggest_topics)
