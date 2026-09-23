from dataclasses import dataclass, field
import random
import uuid

from app.modules.assessment.application.common import guard_edit, load_exam
from app.modules.assessment.domain.entities import ExamQuestion
from app.modules.assessment.domain.ports import ExamRepository, QuestionBank, Subjects
from app.modules.assessment.domain.services import exam_rules
from app.modules.assessment.domain.value_objects import PoolFilter
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class ApplyBlueprint:
    exam_id: uuid.UUID
    rows: list[dict] = field(default_factory=list)  # {topic_id | tag_id, type?, difficulty?, count}
    seed: int | None = None
    replace: bool = True


class ApplyBlueprintHandler:
    """A matrix: each row draws `count` distinct usable questions at random (repeatable with a seed); a row short of
    questions is reported, not refused (US-01, A-01) — unless its topic holds no usable question at all, which is
    refused before anything is touched (pickers-builder A-05)."""

    def __init__(self, exams: ExamRepository, bank: QuestionBank, subjects: Subjects, uow: UnitOfWork):
        self.exams, self.bank, self.subjects, self.uow = exams, bank, subjects, uow

    def __call__(self, actor: Actor, cmd: ApplyBlueprint) -> dict:
        exam = load_exam(self.exams, actor.org_id, cmd.exam_id)
        guard_edit(self.exams, exam)
        exam_rules.check_rows(cmd.rows)
        self._guard_topics(actor, exam, cmd.rows)
        if cmd.replace:
            self.exams.clear(exam.id)
        rng = random.Random(cmd.seed if cmd.seed is not None else random.randrange(1 << 30))
        taken = {eq.question_id for eq in self.exams.questions(exam.id)}
        position = len(taken)
        shortfalls, added = [], 0
        for i, row in enumerate(cmd.rows):
            pool = [qid for qid in self.bank.pool(actor.org_id, exam_rules.row_filter(exam.subject_id, row)) if qid not in taken]
            pick = rng.sample(pool, min(row["count"], len(pool)))
            if len(pick) < row["count"]:
                shortfalls.append({"row": i, "missing": row["count"] - len(pick)})
            types = {q.id: q.type for q in self.bank.questions(None, pick)}
            for qid in pick:
                position += 1
                self.exams.add_question(ExamQuestion(exam_id=exam.id, question_id=qid, position=position,
                                                     section=exam_rules.section_of(types[qid]), points=exam.points_for(types[qid]), row=i))
                taken.add(qid)
                added += 1
        exam.blueprint = cmd.rows
        exam.source = "blueprint" if exam.source == "manual" else exam.source
        exam_rules.renumbered(self.exams.questions(exam.id))
        self.uow.commit()
        return {"added": added, "shortfalls": shortfalls}

    def _guard_topics(self, actor: Actor, exam, rows: list[dict]) -> None:
        """What each row's topic holds in the exam's subject, before the draw narrows it by type or difficulty: a
        topic with nothing usable is named and the whole generation refused (AC-06)."""
        by_row = [(i, t) for i, r in enumerate(rows) if (t := exam_rules.row_topic(r))]
        if not by_row:
            return
        names = self.subjects.topic_names(actor.org_id, list(dict.fromkeys(t for _, t in by_row)))
        held: dict[uuid.UUID, int] = {}
        for i, topic_id in by_row:
            if topic_id not in held:
                held[topic_id] = len(self.bank.pool(actor.org_id, PoolFilter(subject_id=exam.subject_id, topic_id=topic_id)))
            exam_rules.check_topic_pool(i, topic_id, names.get(topic_id), held[topic_id])
