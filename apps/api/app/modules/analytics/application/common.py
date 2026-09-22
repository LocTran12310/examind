"""Steps several analytics use cases share: a student's mastery rows rolled up the topic tree, and the plan of a
personal review exam."""
from collections.abc import Callable
from datetime import datetime, timedelta
import random
import uuid

from app.modules.analytics.domain.ports import AnswerHistory, MasteryRepository, QuestionPool, Topics
from app.modules.analytics.domain.services import mastery as mastery_rules
from app.modules.analytics.domain.services.practice import (
    REASK_AFTER,
    REASK_SHARE,
    RECENT_CORRECT_DAYS,
    WEAK_SHARE,
    WEAK_TOPICS,
    draw,
    shares,
    target_difficulties,
)
from app.modules.analytics.domain.value_objects import Pick, Plan

Clock = Callable[[], datetime]


def mastery_rows(repo: MasteryRepository, topics: Topics, org_id: uuid.UUID, student_id: uuid.UUID) -> list[dict]:
    """Leaf rows plus parents rolled up (answers-weighted), sorted by path."""
    leaves = repo.leaves(org_id, student_id)
    if not leaves:
        return []
    return mastery_rules.rollup(leaves, topics.of_org(org_id))


class PracticePlanner:
    """Which questions a personal review exam asks (adaptive-review ADR-02): about 10 % old mistakes due again (wrong
    ≥ 24 h ago, not answered right since), about 60 % from the three weakest topics (widened to the parent topic when a
    topic runs dry) at difficulties matching the mastery, the rest from topics half-mastered, then anything usable.
    Questions answered right in the last 7 days are left out. Without any mastery yet: a balanced exam over the strands."""

    def __init__(self, mastery: MasteryRepository, topics: Topics, history: AnswerHistory, pool: QuestionPool, clock: Clock):
        self.mastery, self.topics, self.history, self.questions, self.clock = mastery, topics, history, pool, clock

    def build(self, org_id: uuid.UUID, student_id: uuid.UUID, count: int = 20, subject_id: uuid.UUID | None = None,
              seed=None) -> Plan:
        rng = random.Random(seed)
        t = self.clock()
        plan = Plan()
        recent_correct = self.history.recent_correct(org_id, student_id, t - timedelta(days=RECENT_CORRECT_DAYS))
        n_reask_max = round(count * REASK_SHARE)
        usable_wrong = self.history.mistakes_to_reask(org_id, student_id, t - REASK_AFTER, n_reask_max)
        exclude = set(recent_correct)

        mastery = self.mastery.leaves(org_id, student_id)
        if subject_id:
            mastery = [(m, tp) for m, tp in mastery if tp.subject_id == subject_id]
        ranked = sorted(mastery, key=lambda mt: mt[0].mastery)

        n_reask = min(len(usable_wrong), n_reask_max)
        for qid in usable_wrong[:n_reask]:
            plan.picks.append(Pick(qid, "Ôn lại câu từng làm sai"))
        exclude |= plan.ids()

        def pool(path: str | None, excluded: set, subject: uuid.UUID | None = None):
            return self.questions.pool(org_id, path, excluded, subject)

        if not ranked:
            plan.note = "Chưa có dữ liệu làm bài — đề cân bằng các mạch kiến thức, lần sau sẽ theo điểm yếu của bạn."
            strands = [s for s in self.topics.strands(org_id, subject_id) if pool(s.path, exclude)]
            rng.shuffle(strands)
            per = max(1, (count - len(plan.picks)) // max(1, len(strands)))
            for s in strands:
                for qid in draw(rng, pool(s.path, exclude | plan.ids()), per, ["nb", "th"]):
                    plan.picks.append(Pick(qid, "Làm quen", s.name))
            self._fill(rng, plan, org_id, count, exclude, subject_id)
            return plan

        weak = [(m, tp) for m, tp in ranked if m.mastery < 0.8][:WEAK_TOPICS] or ranked[:WEAK_TOPICS]
        medium = [(m, tp) for m, tp in ranked if 0.5 <= m.mastery < 0.8 and (m, tp) not in weak]
        n_weak = round(count * WEAK_SHARE)
        n_medium = count - n_weak - len(plan.picks)

        def take(groups, n, reason):
            if not groups or n <= 0:
                return 0
            got = 0
            for (m, tp), k in zip(groups, shares(n, len(groups))):
                chosen = draw(rng, pool(tp.path, exclude | plan.ids()), k, target_difficulties(m.mastery))
                if len(chosen) < k and tp.parent_id:  # neighbours: widen to the parent subtree
                    parent = self.topics.get(tp.parent_id)
                    chosen += draw(rng, pool(parent.path, exclude | plan.ids() | set(chosen)), k - len(chosen),
                                   target_difficulties(m.mastery))
                for qid in chosen:
                    plan.picks.append(Pick(qid, reason, tp.name))
                got += len(chosen)
            return got

        got_weak = take(weak, n_weak, "Chuyên đề yếu")
        take(medium or weak, n_medium + (n_weak - got_weak), "Củng cố" if medium else "Chuyên đề yếu")
        self._fill(rng, plan, org_id, count, exclude, subject_id)
        return plan

    def _fill(self, rng: random.Random, plan: Plan, org_id: uuid.UUID, count: int, exclude: set, subject_id) -> None:
        missing = count - len(plan.picks)
        if missing > 0:
            for qid in draw(rng, self.questions.pool(org_id, None, exclude | plan.ids(), subject_id), missing, ["th", "vd"]):
                plan.picks.append(Pick(qid, "Bổ sung"))
        if len(plan.picks) < count and not plan.note:
            plan.note = f"Ngân hàng chỉ đủ {len(plan.picks)} câu phù hợp."
