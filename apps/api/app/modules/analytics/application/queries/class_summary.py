from dataclasses import dataclass
import uuid

from app.modules.analytics.application.dto import FactScope, ReportFilters
from app.modules.analytics.application.ports import ReportReader
from app.modules.analytics.domain.services.reports import ratio
from app.shared.application.actor import Actor

WEAKEST = 5  # how many topics the class card names; the full list is a click away in Báo cáo


@dataclass(frozen=True)
class ClassSummary:
    class_id: uuid.UUID


class ClassSummaryHandler:
    """Cả lớp trong một lời gọi: bài giao, lượt đã nộp, điểm trung bình, phổ điểm, và những chuyên đề lớp yếu nhất.

    Các chuyên đề đi qua **đúng phép tính của Báo cáo** (`reader.topics` trên cùng một `FactScope`), không phải một
    phép tính thứ hai viết riêng cho thẻ này. Hai chỗ tính cùng một thứ là hai chỗ sẽ lệch nhau, và người đọc
    không có cách nào biết bên nào đúng.

    Lớp chưa ai nộp trả về `average: None` và phổ điểm toàn 0 — rỗng có cấu trúc, không phải lỗi (AC-04): màn hình
    cần phân biệt được "chưa đo" với "đo rồi và bằng 0".
    """

    def __init__(self, reader: ReportReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: ClassSummary) -> dict:
        scope = FactScope.of(actor, ReportFilters(class_id=query.class_id))
        rows = [{**r, "ratio": ratio(r["points"], r["max_points"])} for r in self.reader.topics(scope, None)]
        # only leaves carry a class's real weakness: a strand's ratio is its children averaged, so it never sinks
        # as low as the one topic underneath it that the class actually cannot do
        leaves = [r for r in rows if r["ratio"] is not None and not any(o["parent_id"] == r["id"] for o in rows)]
        weakest = sorted(leaves, key=lambda r: r["ratio"])[:WEAKEST]
        return {**self.reader.class_summary(scope.org_id, query.class_id),
                "weakest": [{"name": r["name"], "ratio": r["ratio"], "answered": r["answered"]} for r in weakest]}
