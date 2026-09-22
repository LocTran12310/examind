import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.taxonomy.application.dto import GradeRef, SemesterView, SubjectView, TagView, TaxonomyView, TopicView
from app.shared.application.search import Page, SearchRequest
from app.shared.domain.errors import Invalid
from app.shared.infrastructure.schema.taxonomy import grades, school_levels, semesters, subjects, tags, topics
from app.shared.infrastructure.sql_search import Col, search

TAG_COLS = {"group": Col(tags.c.group, "exact"), "name": Col(tags.c.name), "subject_id": Col(tags.c.subject_id, "uuid", sortable=False)}


class SqlTagReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest, subject: str | None, include_shared: bool) -> Page[TagView]:
        stmt = select(tags.c.id, tags.c.group, tags.c.name, tags.c.subject_id).where(tags.c.organization_id == org_id)
        if subject == "shared":
            stmt = stmt.where(tags.c.subject_id.is_(None))
        elif subject:
            try:
                sid = uuid.UUID(subject)
            except ValueError:
                raise Invalid("Môn học không hợp lệ", "subject_id")
            stmt = stmt.where(or_(tags.c.subject_id == sid, tags.c.subject_id.is_(None)) if include_shared else tags.c.subject_id == sid)
        rows, total = search(self.session, stmt, req, TAG_COLS, text=[tags.c.name],
                             default_sort=[tags.c.group, func.lower(tags.c.name), tags.c.id], scalars=False)
        return Page([TagView(id=r.id, group=r.group, name=r.name, subject_id=r.subject_id) for r in rows], total, req.page, req.limit)


class SqlTopicReader:
    def __init__(self, session: Session):
        self.session = session

    def tree(self, org_id: uuid.UUID, subject_id: uuid.UUID | None) -> list[TopicView]:
        stmt = select(topics).where(topics.c.organization_id == org_id)
        if subject_id:
            stmt = stmt.where(topics.c.subject_id == subject_id)
        rows = self.session.execute(stmt.order_by(topics.c.path)).all()
        children: dict = {}
        for r in rows:
            if r.parent_id:
                children[r.parent_id] = children.get(r.parent_id, 0) + 1
        return [TopicView(id=r.id, subject_id=r.subject_id, parent_id=r.parent_id, name=r.name, level_kind=r.level_kind, grade=r.grade,
                          path=r.path, depth=r.path.count(".") + 1, sort=r.sort, child_count=children.get(r.id, 0)) for r in rows]


class SqlTaxonomyReader:
    def __init__(self, session: Session):
        self.session = session

    def get(self, org_id: uuid.UUID) -> TaxonomyView:
        db = self.session
        return TaxonomyView(
            subjects=[SubjectView(r.id, r.code, r.name) for r in db.execute(
                select(subjects).where(subjects.c.organization_id == org_id).order_by(subjects.c.sort))],
            grades=[GradeRef(r.id, r.level, r.name, r.school_level_id, r.level_name) for r in db.execute(
                select(grades, school_levels.c.name.label("level_name")).outerjoin(school_levels, school_levels.c.id == grades.c.school_level_id)
                .where(grades.c.organization_id == org_id).order_by(grades.c.level))],
            semesters=[SemesterView(r.id, r.code, r.name) for r in db.execute(
                select(semesters).where(semesters.c.organization_id == org_id).order_by(semesters.c.sort))],
        )
