"""Read ports of analytics: the reports over the graded answer facts, and the classes and members they list."""
from typing import Protocol
import uuid

from app.modules.analytics.application.dto import FactScope
from app.modules.analytics.domain.value_objects import Member
from app.shared.application.actor import Actor


class Roster(Protocol):
    """Classes (academic) and members (identity) as analytics sees them."""

    def class_members(self, actor: Actor, class_id: uuid.UUID) -> list[Member]:
        """Members of a class of the actor's org, by full name, with their role in the org (unknown class: not found)."""
        ...

    def is_member(self, org_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """An active membership in the org."""
        ...

    def person(self, user_id: uuid.UUID) -> Member | None: ...


class ReportReader(Protocol):
    """Sums over answer_facts, restricted by a FactScope."""

    def topics(self, scope: FactScope, subject_id: uuid.UUID | None) -> list[dict]:
        """Per topic of the org (of the subject): points, max_points, answered over the facts in its subtree, by path."""
        ...

    def unclassified(self, scope: FactScope) -> dict:
        """{p, m, n} of the facts without a topic."""
        ...

    def groups(self, scope: FactScope, by: str) -> list[dict]:
        """{key, label, p, m, n} per question type, difficulty or tag."""
        ...

    def heat(self, scope: FactScope, level: int, subject_id: uuid.UUID | None) -> list[dict]:
        """{student_id, topic_id, name, path, p, m, n} per student and topic of that level, by path."""
        ...

    def class_students(self, org_id: uuid.UUID, class_id: uuid.UUID) -> list[dict]:
        """{id, full_name, username} of the class's active student members, by name."""
        ...

