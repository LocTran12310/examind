---
feature: official-exam-ingestion
adr_count: 5
---

# Logical design — Read official exam files correctly

## Approach
**MathType.** `ingestion/mtef.py` reads the OLE `Equation Native` stream (olefile), parses MTEF v5
records (LINE, CHAR, TMPL, PILE, MATRIX, EMBELL, sizes/fonts/prefs skipped, MathType 7 "future"
records skipped by their 1-byte length) into a small tree and renders LaTeX: fences, intervals,
roots, fractions, bars, arrows, big operators with the glyph in the 4th slot, lim, braces, scripts,
vectors, hats, systems (`cases`), matrices, embellishments; text-style runs become `\text{…}`, runs
that spell a function become `\log`/`\sin`…. `docx.inline_mathtype` swaps every convertible
`<w:object>` in `word/document.xml` for a `⟦EQn⟧` run before Pandoc; the walker restores `$…$`.

**Vector pictures.** `ingestion/vector_images.py`: `to_png(data) -> bytes | None` runs
`soffice --headless --convert-to pdf` in a temp dir (30 s timeout), renders page 1 with pypdfium2
at 2×, trims white margins with Pillow. `assets.document_store` calls it for WMF/EMF (magic bytes)
before `store_image`; `None` keeps today's warning.

**Splitter** (pure, table-tested):
- inside the solutions mode, `PART_RE` still sets the part; a `Câu | n…` row followed by a
  `Đáp án | v…` row is a per-part key (letters, `Đ/S` strings, values) fed to `_parse_key`;
- verdict regex accepts lower-case `đúng/sai` with `|` separators;
- a repeated `(part, 1)` after the last part starts solutions even without a header (existing
  restart rule extended across parts: part I restarting after part III);
- Cyrillic look-alikes (А В С Д → A B C D) normalised in option labels only;
- `Phương pháp:` / `Cách giải:` lines kept as `**Phương pháp:**` headings in the solution.

**Header metadata.** `ingestion/header.py: detect(preamble) -> dict` reads issuer (SỞ/TRƯỜNG
lines), school year (`NĂM HỌC 2024 - 2025`), subject name (`MÔN: TOÁN` → org subject by name),
exam kind (`THI THỬ` → "Thi thử", `GIỮA KỲ`, `CUỐI KỲ`, `KHẢO SÁT`), attempt (`LẦN 1`), grade
(TN THPT → 12, else `LỚP n`/`KHỐI n`), duration. Stored in `doc.meta["detected"]`; empty uploader
fields in `doc.meta` are filled from it (source_name ← issuer) before `persist`, so questions
inherit them. The documents list/review shows the detected values; the uploader can edit meta.

**Upload.** Web `UploadForm` accepts many files (input `multiple`, drop zone); posts them one by
one with the same meta/config, showing per-file status (queued / duplicate / error).

**Exam from document.** `POST /documents/{id}/exam {title?}` → `exams.create(source="document")`
+ questions of the document with USABLE status ordered by part, number; returns
`{exam_id, added, skipped}`. Points come from `DEFAULT_POINTS` (0,25 / 1 / 0,5).

## Alternatives considered
| Option | Why not |
| --- | --- |
| LibreOffice MathType import | Tested: docx→odt keeps OLE replacements, no Math objects |
| mtef-go as a sidecar binary | Adds Go runtime; missing overbar/embell cases seen on the corpus |
| WMF preview via libwmf `wmf2svg` | Tested: fonts and arrows broken |
| New columns for header metadata | `meta` JSONB already carries subject/grade/đợt/năm học/nguồn and feeds persist |
| AI to fill missing answers | Answers are in the file's own tables; rules are exact and free |

## Domain model
| Entity | Change | Notes |
| --- | --- | --- |
| `SourceDocument.meta` | + `detected {issuer, school_year, subject_name, exam_kind, attempt, grade, duration}` | JSONB, no migration |
| `Exam.source` | + value `document`, `settings.source_document_id` | no migration |

## Contracts
| Method & path | Role | Notes |
| --- | --- | --- |
| `POST /documents` | staff | unchanged; called once per file |
| `PATCH /documents/{id}` `{meta}` | staff | edit meta after detection (re-applied to its draft questions) |
| `POST /documents/{id}/exam` `{title?}` | staff | `{exam_id, added, skipped}` |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Equation tokens | extraction run | one job |
| Detected header | `doc.meta.detected` | document |

## Failure modes
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| MTEF not convertible | warning in `doc.log` | — | document warnings |
| soffice missing / timeout | warning | — | document warnings |
| Exam from unparsed document | `validation_error` | 422 | toast |
| No usable question in document | `validation_error` | 422 | toast "Duyệt câu trước" |
| Duplicate file in batch | `duplicate` flag | 200 | per-file row |

## Observability
`doc.log` extract step gains `equations`, `equations_failed`, `vector_images`, `vector_failed`.

## ADRs

### ADR-01 — Own MTEF v5 reader
**Context:** No usable Python package; LibreOffice does not import MathType from docx.
**Decision:** Parse MTEF in `ingestion/mtef.py`, render LaTeX, fall back to the picture per formula.
**Consequences:** 7 889/7 889 corpus formulas read, KaTeX 100 %; new templates need code.
**Status:** accepted

### ADR-02 — Tokens before Pandoc
**Context:** Pandoc keeps the AST we already walk but drops OLE data.
**Decision:** Rewrite `document.xml`, replacing each converted `<w:object>` by a `⟦EQn⟧` text run.
**Consequences:** Formatting around formulas (bold, highlight marking answers) is preserved.
**Status:** accepted

### ADR-03 — LibreOffice renders WMF/EMF
**Context:** Browsers cannot show WMF/EMF; figures carry the question.
**Decision:** soffice → PDF → pypdfium2 PNG, trimmed; optional at runtime.
**Consequences:** Bigger image; conversions ~0.5 s each, only for vector pictures.
**Status:** accepted

### ADR-04 — Answers from the file's own tables
**Context:** Official files put per-part keys inside the solution section.
**Decision:** Read `Câu | … / Đáp án | …` rows per part in solutions mode.
**Consequences:** No AI needed for answers; tables win over formatting, conflicts flagged.
**Status:** accepted

### ADR-05 — Header metadata as suggestions in meta
**Context:** Every official header states issuer, year, subject, kind.
**Decision:** `meta.detected`, applied only to fields the uploader left empty.
**Consequences:** No migration; user input always wins.
**Status:** accepted
