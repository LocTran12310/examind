"""Rules of an uploaded exam file (US-01, A-07, A-08, A-14): accepted kinds, the metadata a teacher may set,
storage names, and which files count as the same one."""
from collections.abc import Callable
import re
import unicodedata
import uuid

from app.shared.domain.errors import Invalid
from app.shared.domain.images import sniff

MAX_BYTES = 30 * 1024 * 1024
EXAM_KINDS = ("Giữa kỳ", "Cuối kỳ", "Khảo sát", "Thi thử", "Ôn tập", "Khác")
KEEP_ON_REPARSE = ("approved",)
ON_DUPLICATE = ("skip", "replace", "keep_both")
QUESTION_META = ("subject_id", "grade", "semester_code", "exam_kind")  # the document's questions follow these
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class UnsupportedFile(Invalid):
    code = "unsupported_file"


class FileTooLarge(Invalid):
    code = "file_too_large"


def detect_kind(filename: str, data: bytes) -> tuple[str, str]:
    """Return (kind, mime) from magic bytes, checked against the extension."""
    name = (filename or "").lower()
    if data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        raise UnsupportedFile("File .doc (Word 97–2003) chưa được hỗ trợ — hãy lưu lại dưới dạng .docx", fields={"file": "Lưu lại dưới dạng .docx"})
    if data[:4] == b"PK\x03\x04" and name.endswith(".docx"):
        return "docx", DOCX
    if data[:5] == b"%PDF-":
        return "pdf", "application/pdf"
    mime, _, _ = sniff(data)
    if mime in ("image/png", "image/jpeg"):
        return "image", mime
    raise UnsupportedFile("Chỉ hỗ trợ .docx, .pdf, .png, .jpg", fields={"file": "Chỉ hỗ trợ .docx, .pdf, .png, .jpg"})


def check_upload(data: bytes, on_duplicate: str) -> None:
    if on_duplicate not in ON_DUPLICATE:
        raise Invalid("Cách xử lý file trùng không hợp lệ", "on_duplicate")
    if not data:
        raise Invalid("File rỗng", "file")
    if len(data) > MAX_BYTES:
        raise FileTooLarge("File tối đa 30MB", "file")


def clean_meta(meta: dict, subject_in_org: Callable[[uuid.UUID], bool], semester_codes: Callable[[], set[str]]) -> dict:
    """The metadata fields a teacher may set, validated; unknown keys are dropped."""
    out: dict = {}
    if meta.get("subject_id"):
        subject_id = uuid.UUID(str(meta["subject_id"]))
        if not subject_in_org(subject_id):
            raise Invalid("Môn học không hợp lệ", "subject_id")
        out["subject_id"] = str(subject_id)
    if meta.get("grade") not in (None, ""):
        grade = int(meta["grade"])
        if not 1 <= grade <= 12:
            raise Invalid("Khối lớp từ 1 đến 12", "grade")
        out["grade"] = grade
    if meta.get("semester_code"):
        if meta["semester_code"] not in semester_codes():
            raise Invalid("Học kỳ không hợp lệ", "semester_code")
        out["semester_code"] = meta["semester_code"]
    if meta.get("exam_kind"):
        if meta["exam_kind"] not in EXAM_KINDS:
            raise Invalid("Loại đề không hợp lệ", "exam_kind")
        out["exam_kind"] = meta["exam_kind"]
    if meta.get("school_year"):
        if not re.fullmatch(r"\d{4}-\d{4}", str(meta["school_year"])):
            raise Invalid("Năm học dạng 2026-2027", "school_year")
        out["school_year"] = meta["school_year"]
    if meta.get("source_name"):
        out["source_name"] = str(meta["source_name"]).strip()[:100]
    return out


def safe_name(filename: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", filename or "file")[-120:]
    return base or "file"


def display_name(filename: str) -> str:
    return (filename or "file")[:300]


def norm_name(name: str) -> str:
    """Same name regardless of Unicode form (macOS gives NFD) and case."""
    return unicodedata.normalize("NFC", name or "").strip().casefold()


def storage_key(org_id: uuid.UUID, document_id: uuid.UUID, filename: str, version: str | None = None) -> str:
    """Object key of a document's file; a replacement gets a version prefix so the old object can be dropped."""
    name = safe_name(filename)
    return f"{org_id}/documents/{document_id}/{version}-{name}" if version else f"{org_id}/documents/{document_id}/{name}"


def page_key(file_key: str, page: int) -> str:
    """Where a PDF page rendered for the review queue is cached, next to the file."""
    return f"{file_key.rsplit('/', 1)[0]}/pages/{page}.png"
