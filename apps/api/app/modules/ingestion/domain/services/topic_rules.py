"""Topic suggestion rules (US-06, A-13): keyword cues per node of the tree, how a tagging model's answer is read, and
when a model may override the keywords."""
import unicodedata

# Extra cues per seeded topic name (lower-case, accents kept). Names themselves are always cues.
SYNONYMS: dict[str, list[str]] = {
    "Hàm số bậc hai và đồ thị": ["parabol", "hàm số bậc hai", "y = x^2", "y = x^{2}", "trục đối xứng"],
    "Tìm đỉnh và trục đối xứng parabol": ["tọa độ đỉnh", "đỉnh của parabol", "trục đối xứng"],
    "Dấu của tam thức bậc hai": ["tam thức", "âm khi", "dương khi"],
    "Mệnh đề": ["mệnh đề", "phủ định", "\\forall", "\\exists"],
    "Tập hợp và các phép toán": ["tập hợp", "\\cap", "\\cup", "∩", "∪", "⊂", "tập con", "giao của", "hợp của"],
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


def _cues(topic) -> list[str]:
    name = _norm(topic.name)
    cues = [name] + [_norm(c) for c in SYNONYMS.get(topic.name, [])]
    return [c for c in cues if len(c) >= 3 or (c and not c.isalnum())]  # single math symbols (∩, ∪) count


def keyword_scores(text: str, topics: list) -> list[tuple[float, object]]:
    """Topics (anything with .name and .path) whose cues occur in the text, best first."""
    t = _norm(text)
    scored = []
    for topic in topics:
        hits = [c for c in _cues(topic) if c in t]
        if hits:
            weight = sum(1 + len(c) / 20 for c in hits) + topic.path.count(".") * 0.05  # prefer deeper nodes on ties
            scored.append((weight, topic))
    return sorted(scored, key=lambda x: -x[0])


TAG_SYSTEM = """Bạn phân loại câu hỏi vào cây chuyên đề. Với mỗi câu, chọn MỘT chỉ số chuyên đề phù hợp nhất
(ưu tiên nhánh sâu nhất đúng). Trả về DUY NHẤT JSON
{"results": [{"number": 1, "index": 12, "name": "tên chuyên đề đúng như ở dòng 12", "confidence": 0.8}]}."""


KNN_MIN_SIMILARITY = 0.35
WEAK_KEYWORD = 0.6


def _resolve(topics: list, idx: int, name):
    """Small models miscount a long numbered list: trust the returned name over the index when they disagree."""
    at = topics[idx] if 0 <= idx < len(topics) else None
    if not isinstance(name, str) or not name.strip():
        return at
    want = _norm(name.split("›")[-1].strip())
    if at is not None and _norm(at.name) == want:
        return at
    named = [t for t in topics if _norm(t.name) == want]
    return named[0] if len(named) == 1 else None


def _label(t, by_id: dict) -> str:
    names, cur = [], t
    while cur is not None:
        names.append(cur.name)
        cur = by_id.get(cur.parent_id)
    return " › ".join(reversed(names))


def _may_replace(local, chosen) -> bool:
    return local is None or chosen.path.startswith(local.path + ".")
