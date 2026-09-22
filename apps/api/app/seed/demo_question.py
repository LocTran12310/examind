"""A sample question per org that exercises every QuestionView feature (AC-24)."""
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.metadata  # noqa: F401  (every table and mapping)
from app.modules.bank.domain.entities import Question
from app.modules.ingestion.application.commands.store_asset import StoreImage
from app.modules.ingestion.infrastructure.adapters.storage import S3FileStorage
from app.modules.ingestion.infrastructure.repositories import SqlAssetRepository
from app.modules.taxonomy.domain.entities import Subject
from app.shared.infrastructure.png import Canvas


def store_image(db: Session, org_id, data: bytes):
    """The picture stored as an asset of the org (ingestion's asset store)."""
    return StoreImage(SqlAssetRepository(db), S3FileStorage())(org_id, data)


def _parabola_png() -> bytes:
    c = Canvas(240, 180)
    ox, oy, s = 60, 120, 30  # origin and scale: x in [-2, 6], y in [-2, 4]
    c.line(0, oy, 239, oy, (150, 150, 150))
    c.line(ox, 0, ox, 179, (150, 150, 150))
    for i in range(0, 1601):
        x = -1 + i * 6 / 1600
        y = x * x - 4 * x + 3
        c.dot(ox + x * s, oy - y * s, (37, 83, 230), 1)
    c.dot(ox + 2 * s, oy + 1 * s, (220, 40, 40), 3)  # vertex I(2; -1)
    return c.encode()


def _triangle_png() -> bytes:
    c = Canvas(220, 160)
    a, b, cc = (30, 140), (190, 140), (80, 30)
    for p, q in ((a, b), (b, cc), (cc, a)):
        c.line(*p, *q, (40, 40, 40), 1)
    for ang in range(0, 60):
        t = math.radians(ang)
        c.dot(a[0] + 18 * math.cos(t), a[1] - 18 * math.sin(t), (220, 40, 40))
    return c.encode()


def seed_demo_question(db: Session, org_id) -> Question | None:
    existing = db.scalar(select(Question).where(Question.organization_id == org_id, Question.source == "demo"))
    if existing:
        return existing
    parabola = store_image(db, org_id, _parabola_png())
    triangle = store_image(db, org_id, _triangle_png())
    math_id = db.scalar(select(Subject.id).where(Subject.organization_id == org_id, Subject.code == "toan"))
    q = Question(
        organization_id=org_id,
        subject_id=math_id,
        type="mcq",
        stem=(
            "Cho hàm số $y = x^2 - 4x + 3$ có đồ thị $(P)$. Biết $(P)$ cắt trục hoành tại hai điểm phân biệt.\n\n"
            "Đồ thị $(P)$ là hình nào dưới đây?"
        ),
        options=[
            {"label": "A", "content": "Đường thẳng $y = 2x - 1$"},
            {"label": "B", "content": "Parabol có đỉnh $I(2;\\,1)$"},
            {"label": "C", "content": f"Parabol có đỉnh $I(2;\\,-1)$\n\n![](asset:{parabola.id})"},
            {"label": "D", "content": "Parabol có đỉnh $I(-2;\\,15)$"},
        ],
        answer={"key": "C"},
        solution=(
            "**Bước 1.** Hoành độ đỉnh: $x_I = -\\dfrac{b}{2a} = -\\dfrac{-4}{2\\cdot 1} = 2$.\n\n"
            "**Bước 2.** Tung độ đỉnh: $y_I = 2^2 - 4\\cdot 2 + 3 = -1$.\n\n"
            "**Bước 3.** Vì $a = 1 > 0$ nên parabol quay bề lõm lên trên, cắt $Ox$ tại $x = 1$ và $x = 3$:\n\n"
            "$$x^2 - 4x + 3 = 0 \\iff (x-1)(x-3) = 0.$$\n\n"
            f"Hình minh họa góc $\\widehat{{BAC}}$ (ví dụ ảnh trong lời giải):\n\n![](asset:{triangle.id})\n\n"
            "Vậy chọn **C**."
        ),
        difficulty="th",
        grade=10,
        status="approved",
        source="demo",
    )
    db.add(q)
    db.flush()
    return q
