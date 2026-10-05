---
feature: question-review
adr_count: 6
---

# Logical design — Question review and bank

## Approach
A `question_quality` module owns the rules shared by ingestion and editing: validate a
question (issues + confidence) and decide its triage status. Ingestion gets a new
`POST_PERSIST` hook that (1) normalises each question into `search_text`, (2) marks
near-duplicates via pg_trgm, (3) triages (`auto_approved` / `needs_review`), (4) samples
spot checks, (5) re-suggests topics by kNN when keywords were weak. Review and bank are two
API routers over the same `questions` table; every mutation goes through a `review` service
that recomputes issues and writes an append-only `review_events` row. The web app gets a
keyboard-driven queue page (one question at a time) and a bank page (filters + editor).

## Alternatives considered
| Option | Why not |
| --- | --- |
| Embedding model (bge-m3) for dedupe/kNN | Needs a model service and GPU/CPU budget on the free VM; trigram similarity is good enough for near-identical exam text |
| Separate review_items table | Duplicates question state; a status column + events table is simpler |
| Elasticsearch/Meilisearch for bank search | Extra service; Postgres trigram + ltree covers 10k–100k questions |
| Per-question page crops for Word files | Word has no layout; would need LibreOffice rendering (heavy) |

## Domain model
| Entity | Fields | Notes |
| --- | --- | --- |
| `Question` (+) | status (+ `auto_approved`, `needs_review`, `approved`, `rejected`, `duplicate`), duplicate_of, search_text, spot_check bool, reviewed_by, reviewed_at, updated_at | GIN trgm index on search_text |
| `SourceDocument` (+) | assigned_to | review assignment |
| `ReviewEvent` | id, organization_id, question_id, user_id, action (approve/reject/edit/answer/topic/restore/spot_ok/spot_fail/bulk), before jsonb, after jsonb, created_at | append-only |

Usable = status in (`auto_approved`, `approved`).

## Contracts
| Method & path | Role | Notes |
| --- | --- | --- |
| `GET /review/documents?mine=` | staff | per-document counts by status + spot checks pending |
| `PATCH /review/documents/{id}` `{assigned_to}` | org_admin | assignment |
| `GET /review/documents/{id}/queue` | staff | ordered flagged + spot-check questions (full ParsedQuestionOut + `source_page_url`) |
| `POST /review/questions/{id}/action` `{action: approve|reject|skip|restore, spot_ok?}` | staff | returns updated question |
| `PATCH /questions/{id}` `{stem?, options?, answer?, solution?, type?, difficulty?, grade?, topic_ids?, primary_topic_id?, tag_ids?}` | staff | recomputes issues/confidence; event |
| `POST /review/documents/{id}/approve-confident` | staff | bulk approve auto_approved |
| `POST /review/documents/{id}/answer-key` `{text}` | staff | `{applied, unmatched:[…]}` |
| `POST /questions/bulk` `{ids, set:{topic_id?, difficulty?, add_tag_ids?, status?}}` | staff | |
| `GET /questions?q=&subject_id=&grade=&semester_code=&exam_kind=&topic_id=&tag_ids=&type=&difficulty=&status=&document_id=&page=` | staff | `Page[ParsedQuestionOut]` |
| `POST /questions` | staff | manual create (approved, source manual) |
| `DELETE /questions/{id}` | staff | hard delete (409 if referenced later by exams) |
| `GET /documents/{id}/pages/{n}.png` | staff | rendered PDF page (cached in MinIO) |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Queue position, pending edits | review page client state | page |
| Question status / issues | API (`review` service) | persistent |
| Threshold | `organizations.settings.ingestion.threshold` | persistent, raised by spot-check loop |

## Failure modes
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Approving a question with blocking issues | `has_blocking_issues` | 409 | toast listing the issues, stays on question |
| Invalid answer for type (e.g. "E" for MCQ) | `validation_error` | 422 | inline |
| Question of another org | `not_found` | 404 | — |
| Delete of a question used by an exam | `question_in_use` | 409 | message |
| Answer key with no matching numbers | 200 with `applied: 0` | — | summary |

## Cache & offline
Rendered PDF pages are stored once in MinIO (`…/pages/{n}.png`) and served with long cache headers.

## Observability
`review_events` feed per-org metrics: flagged ratio per document, actions per reviewed question, spot-check error rate (shown on the review list).

## ADRs

### ADR-01 — pg_trgm for dedupe, kNN and search
**Context:** No model budget; texts are near-identical copies across exams.
**Decision:** `pg_trgm` + `unaccent`; `questions.search_text` = unaccented lower-case stem + options, maintained on write; GIN trigram index.
**Consequences:** Paraphrases are not detected; can swap in embeddings later behind the same service functions.
**Status:** accepted

### ADR-02 — One quality module for ingestion and editing
**Context:** Issues/confidence must stay consistent whether a question came from the splitter or a teacher edit.
**Decision:** `app/services/question_quality.py` validates a question dict; the splitter's `_finalise` delegates to it.
**Consequences:** Editing a question re-evaluates it with exactly the rules that flagged it.
**Status:** accepted

### ADR-03 — Status column + append-only review events
**Context:** Need workflow state and quality metrics.
**Decision:** Workflow lives in `questions.status`; history in `review_events` (never updated).
**Consequences:** Metrics are queries over events; no separate queue table.
**Status:** accepted

### ADR-04 — Keyboard-first single-question queue
**Context:** Success signal is actions per flagged question.
**Decision:** Queue page shows one question, pre-selects suggestions, maps every action to one key, saves on each action (optimistic UI, rollback on error).
**Consequences:** Needs a visible key legend and focus management; mouse actions mirror keys.
**Status:** accepted

### ADR-05 — Two blocking levels: auto-approval vs manual approval
**Context:** Live demo: OCR-flagged but correct questions could not be approved by a teacher.
**Decision:** `blocking()` (stops auto-approval) includes "needs eyes" flags (OCR, AI failure, answer conflicts); `blocking_manual()` only structural problems. A teacher's approval settles the "needs eyes" flags.
**Consequences:** OCR/AI questions always get a human look but never trap the reviewer.
**Status:** accepted

### ADR-06 — OCR-tolerant option labels
**Context:** Tesseract drops the space after option labels ("D.14", "C.Ø").
**Decision:** An option label may be followed directly by a non-space, non-punctuation character; a whitespace before the label is still required so "AB.AC" inside text is not split.
**Consequences:** Scanned exams split fully; inline false positives stay guarded by the A→B→C→D sequence check.
**Status:** accepted
