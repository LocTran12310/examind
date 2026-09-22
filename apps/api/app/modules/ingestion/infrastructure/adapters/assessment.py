"""ExamDrafts over the assessment context's application API. The API object is handed in by the composition root:
ingestion never imports another module."""
from typing import Protocol
import uuid


class _AssessmentApi(Protocol):
    def exam_from_document(self, actor, document_id: uuid.UUID, filename: str, status: str, meta: dict, title: str | None = None) -> dict: ...


class AssessmentExamDrafts:
    def __init__(self, assessment: _AssessmentApi):
        self.assessment = assessment

    def from_document(self, actor, document_id: uuid.UUID, filename: str, status: str, meta: dict, title: str | None) -> dict:
        return self.assessment.exam_from_document(actor, document_id, filename, status, meta, title)
