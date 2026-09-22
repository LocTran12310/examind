"""Steps several bank use cases share: loading a question, placing it in topics / tags, recording review events."""
import uuid

from app.modules.bank.application.dto import BankFilters, ResolvedFilters
from app.modules.bank.domain.entities import Question
from app.modules.bank.domain.ports import QuestionRepository, ReviewLog, ReviewSettings, Taxonomy
from app.modules.bank.domain.services.review import SPOT_WINDOW, raised_threshold
from app.shared.application.actor import Actor
from app.shared.domain.errors import Invalid, NotFound


def load_question(questions: QuestionRepository, org_id: uuid.UUID, question_id: uuid.UUID) -> Question:
    q = questions.get(org_id, question_id)
    if q is None:
        raise NotFound("Không tìm thấy câu hỏi")
    return q


def record(log: ReviewLog, actor: Actor, q: Question | None, action: str, before: dict | None, after: dict | None) -> None:
    log.record(actor.org_id, actor.user_id, q.id if q else None, action, before, after)


def set_topics(questions: QuestionRepository, taxonomy: Taxonomy, log: ReviewLog, actor: Actor, q: Question,
               topic_ids: list[uuid.UUID] | None, primary_id: uuid.UUID | None) -> None:
    """Manual placement: `topic_ids` (None = just the primary one); the primary topic is always among them."""
    ids = list(topic_ids) if topic_ids is not None else ([primary_id] if primary_id else [])
    if primary_id and primary_id not in ids:
        ids.insert(0, primary_id)
    if ids and set(ids) - set(taxonomy.topic_paths(actor.org_id, ids)):
        raise Invalid("Chuyên đề không hợp lệ", "topic_ids")
    primary = primary_id or (ids[0] if ids else None)
    questions.replace_topics(q.id, ids, primary)
    record(log, actor, q, "topic", None, {"topics": [str(i) for i in ids], "primary": str(primary) if primary else None})


def set_tags(questions: QuestionRepository, taxonomy: Taxonomy, actor: Actor, q: Question, tag_ids: list[uuid.UUID]) -> None:
    ids = list(tag_ids)
    if ids and set(ids) - set(taxonomy.tag_groups(actor.org_id, ids)):
        raise Invalid("Tag không hợp lệ", "tag_ids")
    questions.replace_tags(q.id, ids)


def spot_feedback(log: ReviewLog, settings: ReviewSettings, actor: Actor) -> None:
    """A-07: two failed spot checks in the last twenty make auto-approval stricter."""
    old = settings.threshold(actor.org_id)
    new = raised_threshold(log.recent_spot_actions(actor.org_id, SPOT_WINDOW), old)
    if new is not None:
        settings.set_threshold(actor.org_id, new)
        record(log, actor, None, "triage", {"threshold": old}, {"threshold": new})


def resolve_filters(taxonomy: Taxonomy, org_id: uuid.UUID, f: BankFilters) -> ResolvedFilters:
    """Look the chosen topics and tags up in the org: unknown ones are a validation error."""
    paths: tuple[str, ...] = ()
    if f.topic_ids:
        found = taxonomy.topic_paths(org_id, list(f.topic_ids))
        if len(found) != len(set(f.topic_ids)):
            raise Invalid("Chuyên đề không hợp lệ", "topic_ids")
        paths = tuple(found[t] for t in dict.fromkeys(f.topic_ids))
    groups: tuple[tuple[uuid.UUID, ...], ...] = ()
    if f.tag_ids:
        found = taxonomy.tag_groups(org_id, list(f.tag_ids))
        if len(found) != len(set(f.tag_ids)):
            raise Invalid("Tag không hợp lệ", "tag_ids")
        by_group: dict[str, list[uuid.UUID]] = {}
        for tid, group in found.items():
            by_group.setdefault(group, []).append(tid)
        groups = tuple(tuple(v) for v in by_group.values())
    return ResolvedFilters(f, paths, groups)
