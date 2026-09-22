from app.modules.bank.application.commands.triage_questions import TriageQuestions, TriageQuestionsHandler
from app.modules.bank.domain.ports import DuplicateFinder, QuestionRepository
from app.modules.bank.domain.services.quality import evaluate
from app.shared.application.unit_of_work import UnitOfWork

LEGACY_THRESHOLD = 0.85


class TriageLegacyDraftsHandler:
    """Questions stored before the review workflow existed are still `draft`: their quality is re-evaluated (a missing
    solution no longer counts as an issue) and they are triaged once, with a fixed spot-check seed. Flushed, the caller
    commits; the number of drafts."""

    def __init__(self, questions: QuestionRepository, duplicates: DuplicateFinder, uow: UnitOfWork):
        self.questions, self.duplicates, self.uow = questions, duplicates, uow

    def __call__(self) -> int:
        drafts = self.questions.with_status("draft")
        for q in drafts:
            q.issues, q.confidence = evaluate(q.type, q.stem, q.options or [], q.answer, q.solution,
                                              extra_issues=[i for i in q.issues or [] if i != "thiếu lời giải"], ocr=q.parse_method == "ocr")
        if drafts:
            TriageQuestionsHandler(self.duplicates, self.uow)(TriageQuestions(list(drafts), LEGACY_THRESHOLD, "legacy"))
        return len(drafts)
