from dataclasses import dataclass

from app.modules.analytics.domain.ports import MasteryRepository, Topics
from app.modules.analytics.domain.services import mastery as rules
from app.modules.analytics.domain.value_objects import AnswerRecord
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class RecordAnswer:
    answer: AnswerRecord


def record(mastery: MasteryRepository, topics: Topics, a: AnswerRecord) -> bool:
    """The answer moves the student's mastery of its topic; answers without a (known) topic are ignored."""
    if not a.topic_path:
        return False
    topic_id = topics.id_by_path(a.organization_id, a.topic_path)
    if topic_id is None:
        return False
    row = mastery.get(a.student_id, topic_id)
    if row is None:
        row = rules.fresh(a.student_id, topic_id, a.organization_id)
        mastery.add(row)
    rules.apply(row, a.correct_ratio, a.difficulty, a.at)
    return True


class RecordAnswerHandler:
    """Assessment reports every graded answer (its FactListener): the topic mastery follows, flushed with the grading
    transaction (assessment commits)."""

    def __init__(self, mastery: MasteryRepository, topics: Topics, uow: UnitOfWork):
        self.mastery, self.topics, self.uow = mastery, topics, uow

    def __call__(self, cmd: RecordAnswer) -> None:
        if record(self.mastery, self.topics, cmd.answer):
            self.uow.flush()
