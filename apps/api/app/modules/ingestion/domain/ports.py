"""What ingestion needs from the outside world: storage, the extraction tools, AI models, and the other contexts
(the bank keeps the questions, the taxonomy the subjects / topics / tags, assessment the exams)."""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
import uuid

from app.modules.ingestion.domain.entities import AiModel, Asset, SourceDocument
from app.modules.ingestion.domain.services.lines import Line

ImageStore = Callable[[bytes, int | None], str | None]  # (image bytes, page) -> asset id, None when skipped
OcrPage = Callable[[object, int], list[Line]]           # (raster page image, page number) -> lines


# ------------------------------------------------------------------ own data

class DocumentRepository(Protocol):
    def get(self, org_id: uuid.UUID, document_id: uuid.UUID) -> SourceDocument | None: ...

    def get_any(self, document_id: uuid.UUID) -> SourceDocument | None:
        """By id alone (the worker has no org)."""
        ...

    def by_hash(self, org_id: uuid.UUID, file_hash: str) -> SourceDocument | None: ...

    def of_org(self, org_id: uuid.UUID) -> list[SourceDocument]: ...

    def add(self, doc: SourceDocument) -> None: ...

    def remove(self, doc: SourceDocument) -> None: ...


class AssetRepository(Protocol):
    def get(self, org_id: uuid.UUID, asset_id: uuid.UUID) -> Asset | None: ...

    def add(self, asset: Asset) -> None: ...


class AiModelRepository(Protocol):
    def get(self, model_id: uuid.UUID) -> AiModel | None: ...

    def add(self, m: AiModel) -> None: ...

    def remove(self, m: AiModel) -> None: ...


class OrgSettings(Protocol):
    """organizations.settings.ingestion: the org's processing defaults."""

    def ingestion(self, org_id: uuid.UUID) -> dict | None:
        """The stored dict, {} when the org has none, None when the org does not exist."""
        ...

    def save_ingestion(self, org_id: uuid.UUID, values: dict) -> None: ...


class FileStorage(Protocol):
    """Object storage (uploaded files, images, rendered pages)."""

    def put(self, key: str, data: bytes, content_type: str) -> None: ...

    def get(self, key: str) -> tuple[bytes, str]:
        """(bytes, content type); raises when the key is missing."""
        ...

    def delete(self, key: str) -> None:
        """Best effort: failures are ignored."""
        ...


class KeyCipher(Protocol):
    """Encryption of provider API keys at rest."""

    def encrypt(self, plain: str) -> str: ...

    def decrypt(self, token: str | None) -> str | None: ...


# ------------------------------------------------------------------ tools

class DocxReader(Protocol):
    def read(self, data: bytes, store: ImageStore, stats: dict | None = None) -> tuple[list[Line], list[str]]:
        """(lines, warnings); raises DocxError."""
        ...


class PdfReader(Protocol):
    def read(self, data: bytes, store: ImageStore, warnings: list[str], ocr_page: OcrPage | None = None) -> tuple[list[Line], int]:
        """(lines, page count); pages without a text layer go to `ocr_page`. Raises on malformed files."""
        ...


class Scanner(Protocol):
    """Raster images: decoding, Tesseract, PNG encoding (for vision models)."""

    def open(self, data: bytes) -> object:
        """A decoded image; raises on unreadable data."""
        ...

    def tesseract(self, image: object, page: int) -> list[Line]:
        """Raises OcrError."""
        ...

    def png(self, image: object) -> bytes: ...


class VectorImages(Protocol):
    """WMF/EMF pictures (browsers cannot show them) → PNG."""

    def kind(self, data: bytes) -> str | None:
        """'wmf' | 'emf' | None."""
        ...

    def to_png(self, data: bytes) -> bytes | None:
        """PNG bytes, b"" for a blank drawing, None when it cannot be converted."""
        ...


class PageRenderer(Protocol):
    def render_png(self, pdf: bytes, page: int) -> bytes:
        """One PDF page as PNG (review queue)."""
        ...


@dataclass
class ChatResult:
    text: str
    latency_ms: int
    model: str


class ChatModels(Protocol):
    """The providers' chat APIs (ollama / openai-compatible / anthropic)."""

    def chat(self, m: AiModel, system: str, user: str, images: list[bytes] | None = None, json_mode: bool = True,
             timeout: float | None = None, schema: dict | None = None) -> ChatResult:
        """Raises LlmError."""
        ...

    def discover(self, base_url: str) -> list[dict]:
        """Models served by an Ollama instance; raises LlmError."""
        ...


# ------------------------------------------------------------------ other contexts

@dataclass(frozen=True)
class TopicNode:
    id: uuid.UUID
    name: str
    path: str
    parent_id: uuid.UUID | None


class Taxonomy(Protocol):
    """Subjects, semesters, topics and source tags of the org (the taxonomy context)."""

    def subjects(self, org_id: uuid.UUID) -> list[tuple[uuid.UUID, str, str]]:
        """(id, name, code) of the org's subjects."""
        ...

    def subject_in_org(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool: ...

    def semester_codes(self, org_id: uuid.UUID) -> set[str]: ...

    def subject_id_by_code(self, org_id: uuid.UUID, code: str) -> uuid.UUID | None: ...

    def topics(self, org_id: uuid.UUID, subject_id) -> list[TopicNode]:
        """Topics of one subject (subject_id None = topics without a subject), by path."""
        ...

    def topic(self, topic_id: uuid.UUID) -> TopicNode | None: ...

    def source_tag(self, org_id: uuid.UUID, name: str | None) -> uuid.UUID | None:
        """The "source" tag of that name (case-insensitive), created when missing; None without a name."""
        ...


class QuestionBank(Protocol):
    """The bank context: where the parsed questions live."""

    def remove_document_questions(self, document_id: uuid.UUID, keep_statuses: tuple[str, ...], keep_used: bool) -> None:
        """Delete the document's questions except those with a kept status (and, with keep_used, those an exam uses);
        copies marked duplicate of them go back to review."""
        ...

    def kept_positions(self, document_id: uuid.UUID) -> set[tuple[str | None, int | None]]:
        """(part, number) of the document's remaining questions."""
        ...

    def add_parsed(self, org_id: uuid.UUID, document_id: uuid.UUID, drafts: list[dict], tag_id: uuid.UUID | None) -> list[uuid.UUID]:
        """Create one draft question per dict (the question columns), tagged with `tag_id`; ids in order."""
        ...

    def triage(self, question_ids: list[uuid.UUID], threshold: float, seed: str) -> dict:
        """Search text, near-duplicates, auto-approve vs review, spot checks; the counts per outcome."""
        ...

    def nearest_topic(self, question_id: uuid.UUID) -> tuple[uuid.UUID, float] | None:
        """(primary topic, similarity) of the most similar approved question (kNN over search text)."""
        ...

    def nearest_topics(self, org_id: uuid.UUID, subject_id: uuid.UUID | None, question_id: uuid.UUID,
                       limit: int) -> list[tuple[uuid.UUID, float]]:
        """(topic, similarity) of the primary topics of the usable questions of that subject whose text looks most
        like this question's, best first (the tagging queue's kNN)."""
        ...

    def suggest_topic(self, question_id: uuid.UUID, topic_id: uuid.UUID, source: str, score: float) -> None: ...

    def set_difficulty(self, levels: dict[uuid.UUID, tuple[str, str]]) -> dict[str, int]:
        """{question id: (level, auto | ai)} onto those questions; how many took each source. A level a person set
        is left alone (difficulty-at-upload ADR-04), so the answer can be smaller than what was asked for."""
        ...

    def review_untagged(self, question_ids: list[uuid.UUID]) -> int:
        """topic-coverage ADR-02: questions the suggester could not place wait for a teacher; how many moved."""
        ...

    def follow_document(self, document_id: uuid.UUID, changes: dict, old_tag_id: uuid.UUID | None, new_tag_id: uuid.UUID | None) -> None:
        """The document's meta changed: its questions take the new values; the source tag is swapped when given."""
        ...

    def flush(self) -> None: ...


class ExamDrafts(Protocol):
    """The assessment context: a draft exam from a parsed document."""

    def from_document(self, actor, document_id: uuid.UUID, filename: str, status: str, meta: dict, title: str | None) -> dict:
        """{exam_id, added, skipped}; the document's usable questions in PHẦN / Câu order (flushed with the caller's transaction)."""
        ...
