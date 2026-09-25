from dataclasses import dataclass

from app.modules.bank.application.dto import BackfillResult
from app.modules.bank.domain.ports import DifficultyLevels, QuestionRepository
from app.modules.bank.domain.services.review import fill_difficulty
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Forbidden, Invalid

DEFAULT_LIMIT = 200
MAX_LIMIT = 500
#: with the model on, the run is bounded much tighter: measured at ~0.9s a question on the owner's bank, so 100 is
#: already a minute and a half of one HTTP request. The answer says what is left; the caller runs it again.
MAX_LIMIT_WITH_MODEL = 100


@dataclass(frozen=True)
class BackfillDifficulty:
    limit: int = DEFAULT_LIMIT
    use_model: bool = False


class BackfillDifficultyHandler:
    """Give a level to questions that have none (difficulty-at-upload US-03, AC-05, A-06).

    Questions already in the bank never went through the pipeline's difficulty pass, so they sit with `difficulty`
    null — 379 of the owner's 381 usable questions did — and every blueprint row asking for a mức độ came up short
    against them. This is the one command that fixes that without re-uploading a single paper.

    **It only ever touches a question whose level is empty.** That is what makes it safe to re-run and what makes
    a second run report `filled: 0`: nothing to do is the normal outcome. A level a teacher set is protected twice
    over — such a question is not empty, so it is never selected, and `fill_difficulty` would refuse it anyway
    (ADR-04).

    **It writes no review event.** The history behind "Thay đổi gần đây" is a teacher's own trail and the source of
    "Hoàn tác"; a few hundred machine rows would bury the edits a teacher actually wants to find. There is also
    nothing to undo *to*: the field was empty, and undoing back to empty would only be re-filled by the next run.
    The provenance that matters is on the question itself, in `difficulty_source`.

    The run is bounded so it finishes inside one request, and `remaining` is how the caller knows to go again.
    """

    def __init__(self, questions: QuestionRepository, levels: DifficultyLevels, uow: UnitOfWork):
        self.questions, self.levels, self.uow = questions, levels, uow

    def __call__(self, actor: Actor, cmd: BackfillDifficulty) -> BackfillResult:
        if actor.role != "org_admin":
            raise Forbidden("Chỉ quản trị viên của trung tâm mới chạy được lệnh này")
        ceiling = MAX_LIMIT_WITH_MODEL if cmd.use_model else MAX_LIMIT
        if cmd.limit < 1 or cmd.limit > ceiling:
            raise Invalid(f"Mỗi lần chạy từ 1 đến {ceiling} câu", "limit")
        qs = self.questions.without_difficulty(actor.org_id, cmd.limit)
        if not qs:
            return BackfillResult(0, {}, 0, False)
        asked = [(q.id, q.part, q.number, q.type, q.stem, q.options or []) for q in qs]
        chosen, model_used = self.levels.levels_for(actor.org_id, asked, cmd.use_model)
        by_source: dict[str, int] = {}
        for q in qs:
            level, source = chosen.get(q.id, (None, "auto"))
            if level and fill_difficulty(q, level, source):
                by_source[source] = by_source.get(source, 0) + 1
        self.uow.commit()
        filled = sum(by_source.values())
        # counted after the write, so it reflects what this run actually left behind rather than what it meant to do
        return BackfillResult(filled, by_source, self.questions.count_without_difficulty(actor.org_id), model_used)
