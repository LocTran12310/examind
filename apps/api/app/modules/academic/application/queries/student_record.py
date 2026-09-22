from dataclasses import dataclass
import uuid

from app.modules.academic.application.ports import RecordReader
from app.modules.academic.domain.ports import MemberDirectory
from app.shared.application.actor import STAFF_ROLES, Actor
from app.shared.domain.errors import Forbidden, NotFound


@dataclass(frozen=True)
class StudentRecord:
    student_id: uuid.UUID


class StudentRecordHandler:
    """Hồ sơ học sinh (school-years US-04): staff, or the student themself."""

    def __init__(self, directory: MemberDirectory, reader: RecordReader):
        self.directory, self.reader = directory, reader

    def __call__(self, actor: Actor, query: StudentRecord) -> dict:
        if actor.role not in STAFF_ROLES and not (actor.role == "student" and actor.user_id == query.student_id):
            raise Forbidden()
        if not self.directory.member_ids(actor.org_id, {query.student_id}):
            raise NotFound("Không tìm thấy học sinh")
        return self.reader.record(actor.org_id, query.student_id)
