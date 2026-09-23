"""Steps several analytics use cases share: a student's mastery rows rolled up the topic tree, and the plan of a
personal review exam."""
from collections.abc import Callable
from datetime import datetime, timedelta
import random
import uuid

from app.modules.analytics.domain.ports import AnswerHistory, MasteryRepository, QuestionPool, Topics
from app.modules.analytics.domain.services import mastery as mastery_rules
from app.modules.analytics.domain.services.practice import (
    CONSOLIDATE_BELOW,
    PLAN_TOPICS,
    REASK_AFTER,
    REASK_SHARE,
    RECENT_CORRECT_DAYS,
    WEAK_SHARE,
    draw,
    shares,
    target_difficulties,
)
from app.modules.analytics.domain.value_objects import Pick, Plan

Clock = Callable[[], datetime]


def mastery_rows(repo: MasteryRepository, topics: Topics, org_id: uuid.UUID, student_id: uuid.UUID,
                 at: datetime | None = None) -> list[dict]:
    """Leaf rows plus parents rolled up (answers-weighted), sorted by path, decayed to `at` (ADR-04)."""
    leaves = repo.leaves(org_id, student_id)
    if not leaves:
        return []
    return mastery_rules.rollup(leaves, topics.of_org(org_id), at)


class PracticePlanner:
    """Which questions a personal review exam asks (adaptive-review ADR-02): about 10 % old mistakes due again (wrong
    ≥ 24 h ago, not answered right since), about 60 % from the three weakest topics (learning-telemetry ADR-04: weak
    means enough answers too, so a thin topic is never planned around) widened to the parent topic when a topic runs
    dry, at difficulties matching the mastery, the rest from topics half-mastered, then anything usable.
    Questions answered right in the last 7 days are left out. Without enough data yet: a balanced exam over the strands."""

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

        def level(mt) -> tuple[float, int]:
            m = mt[0]
            return mastery_rules.decay(m.mastery, m.last_at, t), (m.answers or 0)

        ranked = sorted(mastery, key=lambda mt: level(mt)[0])

        n_reask = min(len(usable_wrong), n_reask_max)
        for qid in usable_wrong[:n_reask]:
            plan.picks.append(Pick(qid, "Ôn lại câu từng làm sai"))
        exclude |= plan.ids()

        def pool(path: str | None, excluded: set, subject: uuid.UUID | None = None):
            return self.questions.pool(org_id, path, excluded, subject)

        weak = mastery_rules.weak_topics(ranked, PLAN_TOPICS, level)
        medium = [mt for mt in ranked if mastery_rules.enough(level(mt)[1]) and mt not in weak
                  and mastery_rules.START <= level(mt)[0] < CONSOLIDATE_BELOW]
        if not weak and not medium:  # nothing measured well enough to plan around
            plan.note = ("Chưa có dữ liệu làm bài — đề cân bằng các mạch kiến thức, lần sau sẽ theo điểm yếu của bạn."
                         if not ranked else
                         "Chưa đủ dữ liệu theo chuyên đề — đề cân bằng các mạch kiến thức, làm thêm để hệ thống hiểu điểm yếu của bạn.")
            self._balanced(rng, plan, org_id, count, exclude, subject_id)
            self._fill(rng, plan, org_id, count, exclude, subject_id)
            return plan

        n_weak = round(count * WEAK_SHARE)
        n_medium = count - n_weak - len(plan.picks)

        def take(groups, n, reason):
            if not groups or n <= 0:
                return 0
            got = 0
            for mt, k in zip(groups, shares(n, len(groups))):
                tp = mt[1]
                chosen = draw(rng, pool(tp.path, exclude | plan.ids()), k, target_difficulties(level(mt)[0]))
                if len(chosen) < k and tp.parent_id:  # neighbours: widen to the parent subtree
                    parent = self.topics.get(tp.parent_id)
                    chosen += draw(rng, pool(parent.path, exclude | plan.ids() | set(chosen)), k - len(chosen),
                                   target_difficulties(level(mt)[0]))
                for qid in chosen:
                    plan.picks.append(Pick(qid, reason, tp.name))
                got += len(chosen)
            return got

        got_weak = take(weak, n_weak, "Chuyên đề yếu")
        take(medium or weak, n_medium + (n_weak - got_weak), "Củng cố" if medium else "Chuyên đề yếu")
        self._fill(rng, plan, org_id, count, exclude, subject_id)
        return plan

    def _balanced(self, rng: random.Random, plan: Plan, org_id: uuid.UUID, count: int, exclude: set, subject_id) -> None:
        """A beginner's exam spread over the strands, for a student no topic knows enough about yet."""
        strands = [s for s in self.topics.strands(org_id, subject_id) if self.questions.pool(org_id, s.path, exclude)]
        rng.shuffle(strands)
        per = max(1, (count - len(plan.picks)) // max(1, len(strands)))
        for s in strands:
            for qid in draw(rng, self.questions.pool(org_id, s.path, exclude | plan.ids()), per, ["nb", "th"]):
                plan.picks.append(Pick(qid, "Làm quen", s.name))

    def _fill(self, rng: random.Random, plan: Plan, org_id: uuid.UUID, count: int, exclude: set, subject_id) -> None:
        missing = count - len(plan.picks)
        if missing > 0:
            for qid in draw(rng, self.questions.pool(org_id, None, exclude | plan.ids(), subject_id), missing, ["th", "vd"]):
                plan.picks.append(Pick(qid, "Bổ sung"))
        if len(plan.picks) < count and not plan.note:
            plan.note = f"Ngân hàng chỉ đủ {len(plan.picks)} câu phù hợp."
