"""Topic tree handlers against in-memory ports: paths, depth limit, moves, merge and delete guards (ADR-02)."""
import uuid

import pytest

from app.modules.taxonomy.application.commands.create_topic import CreateTopic, CreateTopicHandler
from app.modules.taxonomy.application.commands.delete_topic import DeleteTopic, DeleteTopicHandler
from app.modules.taxonomy.application.commands.merge_topic import MergeTopic, MergeTopicHandler
from app.modules.taxonomy.application.commands.move_topic import MoveTopic, MoveTopicHandler
from app.modules.taxonomy.application.commands.update_topic import UpdateTopic, UpdateTopicHandler
from app.modules.taxonomy.domain.topics import MAX_TOPIC_DEPTH
from app.shared.application.actor import Actor
from app.shared.domain.errors import Conflict, Invalid, NotFound
from tests.unit.fakes import FakeAudit, FakeUow

ORG = uuid.uuid4()
MATH, PHYS = uuid.uuid4(), uuid.uuid4()
ACTOR = Actor(user_id=uuid.uuid4(), org_id=ORG, role="teacher")


class FakeTopics:
    def __init__(self):
        self.rows = {}

    def get(self, org_id, topic_id):
        t = self.rows.get(topic_id)
        return t if t and t.organization_id == org_id else None

    def children(self, topic_id):
        return sorted((t for t in self.rows.values() if t.parent_id == topic_id), key=lambda t: t.sort)

    def has_children(self, topic_id):
        return any(t.parent_id == topic_id for t in self.rows.values())

    def next_sort(self, org_id, parent_id):
        return max((t.sort for t in self.rows.values() if t.parent_id == parent_id), default=-1) + 1

    def _subtree(self, t):
        return [x for x in self.rows.values() if x.path == t.path or x.path.startswith(t.path + ".")]

    def subtree_depth(self, t):
        return max(x.depth for x in self._subtree(t)) - t.depth

    def move(self, t, parent_id, new_path):
        old = t.path
        for x in self._subtree(t):
            x.path = new_path + x.path[len(old):]
        t.parent_id = parent_id

    def add(self, t):
        self.rows[t.id] = t

    def remove(self, t):
        del self.rows[t.id]


class FakeSubjects:
    def exists(self, org_id, subject_id):
        return org_id == ORG and subject_id in (MATH, PHYS)


class FakeReferences:
    def __init__(self):
        self.used, self.moved = set(), []

    def count(self, org_id, topic_ids):
        return sum(1 for t in topic_ids if t in self.used)

    def repoint(self, org_id, from_id, to_id):
        self.moved.append((from_id, to_id))


@pytest.fixture
def ports():
    return FakeTopics(), FakeSubjects(), FakeReferences(), FakeAudit(), FakeUow()


def test_create_builds_paths_kinds_and_checks_subject_and_depth(ports):
    topics, subjects, _, audit, uow = ports
    create = CreateTopicHandler(topics, subjects, audit, uow)
    root = create(ACTOR, CreateTopic("Giải tích", MATH))
    child = create(ACTOR, CreateTopic("  Nguyên hàm ", PHYS, parent_id=root.id, grade=12))  # the parent's subject wins
    assert (root.depth, root.level_kind, root.sort) == (1, "strand", 0)
    assert child.path.startswith(root.path + ".") and child.subject_id == MATH and child.name == "Nguyên hàm" and child.level_kind == "topic"
    assert create(ACTOR, CreateTopic("Tích phân", MATH, parent_id=root.id)).sort == 1
    with pytest.raises(Invalid):
        create(ACTOR, CreateTopic("x", uuid.uuid4()))
    with pytest.raises(Invalid):
        create(ACTOR, CreateTopic("   ", MATH))
    with pytest.raises(NotFound):
        create(ACTOR, CreateTopic("x", parent_id=uuid.uuid4()))
    parent = child
    for i in range(MAX_TOPIC_DEPTH - 2):
        parent = create(ACTOR, CreateTopic(f"d{i + 3}", parent_id=parent.id))
    assert parent.depth == MAX_TOPIC_DEPTH
    with pytest.raises(Invalid):
        create(ACTOR, CreateTopic("too deep", parent_id=parent.id))
    assert audit.actions().count("topic.create") == 3 + MAX_TOPIC_DEPTH - 2 and uow.commits == audit.actions().count("topic.create")


def test_move_rewrites_the_subtree_and_refuses_cycles_other_subjects_and_depth(ports):
    topics, subjects, _, audit, uow = ports
    create = CreateTopicHandler(topics, subjects, audit, uow)
    move = MoveTopicHandler(topics, audit, uow)
    gt = create(ACTOR, CreateTopic("Giải tích", MATH))
    nh = create(ACTOR, CreateTopic("Nguyên hàm", MATH, parent_id=gt.id))
    cb = create(ACTOR, CreateTopic("Cơ bản", MATH, parent_id=nh.id))
    tp = create(ACTOR, CreateTopic("Tích phân", MATH, parent_id=gt.id))
    moved = move(ACTOR, MoveTopic(nh.id, tp.id))
    assert moved.parent_id == tp.id and moved.depth == 3 and topics.rows[cb.id].path.startswith(moved.path + ".")
    with pytest.raises(Conflict) as e:
        move(ACTOR, MoveTopic(gt.id, cb.id))
    assert e.value.code == "invalid_move"
    other = create(ACTOR, CreateTopic("Cơ học", PHYS))
    with pytest.raises(Conflict):
        move(ACTOR, MoveTopic(nh.id, other.id))
    assert move(ACTOR, MoveTopic(nh.id, None)).depth == 1  # back to a strand
    chain = gt
    for i in range(MAX_TOPIC_DEPTH - 1):
        chain = create(ACTOR, CreateTopic(f"c{i}", parent_id=chain.id))
    with pytest.raises(Conflict):  # nh has a child: depth 5 + 1 is too deep
        move(ACTOR, MoveTopic(nh.id, topics.rows[chain.parent_id].id))
    assert "topic.move" in audit.actions()


def test_update_merge_and_delete_guards(ports):
    topics, subjects, refs, audit, uow = ports
    create = CreateTopicHandler(topics, subjects, audit, uow)
    gt = create(ACTOR, CreateTopic("Giải tích", MATH))
    nh = create(ACTOR, CreateTopic("Nguyên hàm", MATH, parent_id=gt.id))
    cb = create(ACTOR, CreateTopic("Cơ bản", MATH, parent_id=nh.id))
    tp = create(ACTOR, CreateTopic("Tích phân", MATH, parent_id=gt.id))
    assert UpdateTopicHandler(topics, uow)(ACTOR, UpdateTopic(tp.id, name="Tích phân xác định", grade=0)).grade is None
    delete = DeleteTopicHandler(topics, refs, audit, uow)
    with pytest.raises(Conflict) as e:
        delete(ACTOR, DeleteTopic(nh.id))
    assert e.value.code == "topic_has_children"
    refs.used.add(cb.id)
    with pytest.raises(Conflict) as e:
        delete(ACTOR, DeleteTopic(cb.id))
    assert e.value.code == "topic_in_use"
    merge = MergeTopicHandler(topics, refs, audit, uow)
    with pytest.raises(Conflict):
        merge(ACTOR, MergeTopic(gt.id, nh.id))  # into its own subtree
    target = merge(ACTOR, MergeTopic(nh.id, tp.id))
    assert target.id == tp.id and nh.id not in topics.rows and topics.rows[cb.id].parent_id == tp.id
    assert refs.moved == [(nh.id, tp.id)] and "topic.merge" in audit.actions()
    stranger = Actor(user_id=uuid.uuid4(), org_id=uuid.uuid4(), role="teacher")
    with pytest.raises(NotFound):
        delete(stranger, DeleteTopic(tp.id))
