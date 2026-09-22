"""Tag handlers against in-memory ports: no database, no HTTP (architecture-refactor ADR-02)."""
import uuid

import pytest

from app.modules.taxonomy.application.commands.create_tag import CreateTag, CreateTagHandler
from app.modules.taxonomy.application.commands.delete_tag import DeleteTag, DeleteTagHandler
from app.modules.taxonomy.application.commands.update_tag import UpdateTag, UpdateTagHandler
from app.shared.application.actor import Actor
from app.shared.domain.errors import Conflict, Invalid, NotFound

ORG = uuid.uuid4()
ACTOR = Actor(user_id=uuid.uuid4(), org_id=ORG, role="teacher")
SUBJECT = uuid.uuid4()


class FakeTags:
    def __init__(self):
        self.rows = {}

    def get(self, org_id, tag_id):
        t = self.rows.get(tag_id)
        return t if t and t.organization_id == org_id else None

    def name_taken(self, org_id, group, name, exclude_id=None):
        return any(t.organization_id == org_id and t.group == group and t.name.lower() == name.lower() and t.id != exclude_id
                   for t in self.rows.values())

    def add(self, tag):
        self.rows[tag.id] = tag

    def remove(self, tag):
        del self.rows[tag.id]


class FakeSubjects:
    def exists(self, org_id, subject_id):
        return org_id == ORG and subject_id == SUBJECT


class FakeUow:
    commits = 0

    def commit(self):
        self.commits += 1

    def flush(self):
        pass


@pytest.fixture
def ports():
    return FakeTags(), FakeSubjects(), FakeUow()


def test_create_checks_group_name_uniqueness_and_subject(ports):
    tags, subjects, uow = ports
    create = CreateTagHandler(tags, subjects, uow)
    t = create(ACTOR, CreateTag("method", "  Đổi biến ", SUBJECT))
    assert t.name == "Đổi biến" and t.subject_id == SUBJECT and uow.commits == 1
    with pytest.raises(Conflict):
        create(ACTOR, CreateTag("method", "ĐỔI BIẾN"))
    with pytest.raises(Invalid):
        create(ACTOR, CreateTag("bogus", "x"))
    with pytest.raises(Invalid):
        create(ACTOR, CreateTag("custom", "x", uuid.uuid4()))
    assert create(ACTOR, CreateTag("source", "Sở GD", SUBJECT)).subject_id is None  # nguồn đề stays shared


def test_update_and_delete_stay_inside_the_org(ports):
    tags, subjects, uow = ports
    t = CreateTagHandler(tags, subjects, uow)(ACTOR, CreateTag("method", "A", SUBJECT))
    update = UpdateTagHandler(tags, subjects, uow)
    assert update(ACTOR, UpdateTag(t.id, name="B")).subject_id == SUBJECT
    assert update(ACTOR, UpdateTag(t.id, subject_id=None)).subject_id is None
    stranger = Actor(user_id=uuid.uuid4(), org_id=uuid.uuid4(), role="teacher")
    with pytest.raises(NotFound):
        update(stranger, UpdateTag(t.id, name="C"))
    DeleteTagHandler(tags, uow)(ACTOR, DeleteTag(t.id))
    assert not tags.rows
