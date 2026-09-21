---
feature: exam-ingestion
adr_count: 9
---

# Logical design — Exam ingestion

## Approach
Upload stores the original in MinIO, creates a `source_documents` row and enqueues an
`ingest_document` job in a Postgres `jobs` table. A `worker` container (same image as the
API) claims jobs with `SELECT … FOR UPDATE SKIP LOCKED` and runs a four-stage pipeline:

1. **Extract** (format-specific) → a canonical *line stream*: `Line(text, page, kind)` where
   `text` is Markdown with `$…$` math and `![](asset:<id>)` images already uploaded, plus
   formatting hints (`underline`/`bold` spans) that matter for answer detection.
   - docx → Pandoc (`docx → markdown`, OMML → TeX, `--extract-media`) + images stored as assets.
   - text PDF → pdfplumber words/lines in reading order (two-column aware) + pypdfium2 crops for image boxes.
   - scan/image → pypdfium2 render (300 dpi) → OCR provider (Tesseract `vie` by default, or an AI-vision model).
2. **Split** (pure, rule-based, no I/O) → `ParsedQuestion` list: part, number, type, stem,
   options, answer (+ source), solution, confidence, issues. Handles inline answers, trailing
   answer keys, trailing solution sections, formatting-marked answers, THPT-2025 parts.
3. **AI fallback** (optional, per config) for questions below the threshold, via the
   provider chosen at upload, with ordered fallbacks.
4. **Persist + suggest** → replace the document's draft questions (never approved ones),
   inherit metadata, add source tag, suggest a leaf topic (keyword rules, then the tagging model).

Each stage appends to `source_documents.log` (step, ms, counts, warnings).

## Alternatives rejected
| Option | Why not |
| --- | --- |
| Redis + Celery | One more service to run on a 1-VM deployment; Postgres queue is enough at this volume |
| Docling / marker for PDFs | Torch + model downloads (GBs) on a free ARM VM; pdfplumber is enough for text PDFs |
| PyMuPDF | AGPL; the service is network-facing |
| PaddleOCR | Heavy, weak arm64 wheels; Tesseract `vie` is apt-installable; AI-vision OCR is pluggable |
| LiteLLM | 30+ transitive deps for three wire protocols we can adapt in ~150 lines |
| LLM-first splitting | Slow and non-deterministic on free local models; rules handle the regular 90%+ |

## Domain model
| Entity | Fields | Notes |
| --- | --- | --- |
| `Job` | id, kind, payload jsonb, status queued/running/done/failed, attempts, max_attempts, run_after, locked_at, locked_by, error, created_at, finished_at | generic queue |
| `SourceDocument` | id, org, filename, mime, size, file_hash, storage_key, status uploaded/queued/processing/parsed/failed, error, metadata jsonb (subject_id, grade, semester_code, exam_kind, school_year, source_name), processing_config jsonb, page_count, question_count, log jsonb, uploaded_by, created_at, finished_at | unique (org, file_hash) |
| `AiModel` | id, organization_id nullable, name, provider ollama/openai/anthropic, model, base_url, api_key_enc, capabilities text[] (text, vision), is_free, enabled, created_at | NULL org = system-wide |
| `Question` (+) | source_document_id, number, part, semester_code, exam_kind, confidence, issues jsonb, parse_method rule/llm/ocr, parse_model, answer_source | existing table extended |
| `QuestionTopic` | question_id, topic_id, is_primary, source auto/manual, score | PK (question_id, topic_id) |
| `QuestionTag` | question_id, tag_id | PK both |
| `Asset` (+) | source_document_id, page | provenance for crops |

`ProcessingConfig` = `{split_mode: rule|rule_ai|ai, ocr: auto|tesseract|vision, split_models: [ai_model_id…], tag_model: id|null, vision_model: id|null, threshold: 0.85}`.
Org defaults live in `organizations.settings.ingestion`.

## Contracts
| Method & path | Role | Notes |
| --- | --- | --- |
| `POST /documents` multipart `file` + form `meta` (JSON) + `config` (JSON) | staff | 201 `{document, duplicate: false}` or 200 `{document, duplicate: true}` |
| `GET /documents?status=&q=&page=` | staff | list with counts |
| `GET /documents/{id}` | staff | detail incl. log, config, metadata |
| `GET /documents/{id}/questions` | staff | parsed questions with confidence, issues, suggested topics |
| `GET /documents/{id}/file` | staff | original download |
| `POST /documents/{id}/reparse` `{config}` | staff | 202; replaces drafts |
| `DELETE /documents/{id}` | staff | removes drafts + file; approved questions kept, unlinked |
| `GET /ai-models` | staff | available = system + own org; keys never returned (`has_key`) |
| `POST /ai-models`, `PATCH/DELETE /ai-models/{id}` | org_admin (own) / super_admin (system) | |
| `POST /ai-models/discover` `{base_url}` | org_admin, super_admin | lists Ollama `/api/tags` |
| `POST /ai-models/{id}/test` | staff | `{ok, latency_ms, error?}` |
| `GET/PUT /org/settings/ingestion` | GET staff, PUT org_admin | defaults |

LLM split schema (JSON the model must return):
`{"type":"mcq|true_false|short_answer|essay","stem":str,"options":[{"label":str,"content":str,"is_true":bool|null}],"answer":str|null,"solution":str|null}`

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Document status/log | worker, via `source_documents` | persistent |
| Job lock | `jobs.locked_at/by` | until done/failed or 15-min stale |
| Upload form config | client state, seeded from org defaults | page |
| Document status on UI | polled every 2 s while queued/processing | page |

## Error taxonomy
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Unsupported type (.doc, .exe…) | `unsupported_file` | 422 | field error with accepted types |
| Too large / too many pages | `file_too_large` | 422 | field error |
| Parser failure after retries | document `status=failed`, `error` | — | "Lỗi" badge + message + retry button |
| Model unreachable / bad JSON | issue `AI không phản hồi` on questions | — | issue chip |
| Model not visible to org | `not_found` | 404 | — |
| Editing a system model as org_admin | `forbidden` | 403 | — |
| Missing `APP_ENCRYPTION_KEY` when saving a key | `encryption_unavailable` | 500 | message |

## Cache & offline
Duplicate uploads short-circuit by sha256 per org. Pandoc/OCR outputs are not cached beyond
the stored questions; a re-parse recomputes.

## Observability
`source_documents.log` per stage with timings and counts; worker logs job id, doc id, org,
stage, duration; LLM calls log provider, model, latency, tokens if reported — never prompts
with personal data beyond exam text, never API keys.

## ADRs

### ADR-01 — Postgres job queue
**Context:** Background parsing on a single VM.
**Decision:** `jobs` table + `FOR UPDATE SKIP LOCKED`, `worker` service polling every 2 s, `INGEST_CONCURRENCY` threads, stale-lock recovery at 15 min, 3 attempts.
**Consequences:** No Redis; jobs are queryable with SQL; throughput is limited but enough.
**Status:** accepted

### ADR-02 — Canonical line stream between extractors and the splitter
**Context:** Three input formats, one splitting logic.
**Decision:** Extractors emit Markdown lines (math as `$…$`, images as `asset:` refs, underline/bold spans kept); the splitter is a pure function over lines and is unit-tested without files.
**Consequences:** New formats only need an extractor; splitter tests are fast.
**Status:** accepted

### ADR-03 — Thin LLM adapters instead of LiteLLM
**Context:** The plan named LiteLLM; we need Ollama, OpenAI-compatible and Anthropic only.
**Decision:** `app/ingestion/llm.py` with three adapters over httpx, JSON-mode prompting and a validator; providers are rows in `ai_models`.
**Consequences:** Fewer dependencies on the ARM image; adding a protocol is one class. Deviation from the chat plan recorded for final review.
**Status:** accepted

### ADR-04 — pdfplumber + pypdfium2 for PDFs
**Context:** Need text-in-reading-order and image crops without AGPL or torch.
**Decision:** pdfplumber (MIT) for words/lines/image boxes, pypdfium2 (Apache/BSD) to render pages and crops.
**Consequences:** Complex layouts (tables of options) rely on our column heuristics.
**Status:** accepted

### ADR-05 — Tesseract as default OCR, AI vision optional
**Context:** Free, arm64-friendly OCR with Vietnamese.
**Decision:** `tesseract-ocr-vie` in the image, invoked via CLI (TSV with confidences); `vision` engine sends page images to a vision-capable registry model.
**Consequences:** Scanned math is weak; such questions are always flagged for review.
**Status:** accepted

### ADR-06 — API tests run inside the api image
**Context:** Ingestion tests need pandoc and tesseract; the host should stay clean.
**Decision:** `api` Dockerfile gets a `test` stage (dev deps); compose profile `test` service `api-test` mounts `apps/api`; `scripts/verify.sh` runs pytest there.
**Consequences:** Tests match production binaries; each run pays ~3 s container start.
**Status:** accepted

### ADR-07 — Encrypted provider keys
**Context:** Paid providers need API keys stored per org.
**Decision:** Fernet with `APP_ENCRYPTION_KEY` (env); API returns only `has_key`.
**Consequences:** Losing the env key means re-entering provider keys.
**Status:** accepted

### ADR-08 — Pillow allowed in the API image
**Context:** PDF crops and OCR preprocessing need image operations; pypdfium2 renders to PIL.
**Decision:** Use Pillow (already a pdfplumber dependency); the stdlib PNG writer stays for generated demo images.
**Consequences:** Supersedes the "no Pillow" note of platform-foundation ADR-07; SVG uploads remain rejected.
**Status:** accepted

### ADR-09 — Bounded LLM generations and schema-constrained output
**Context:** Live test: small local models in JSON mode ran until the 120 s timeout and drifted from the schema.
**Decision:** `num_predict`/`max_tokens` = 1500, Ollama structured outputs with a JSON schema, normalisation of common drifts (type aliases, numeric labels), timeout from `LLM_TIMEOUT_SECONDS`.
**Consequences:** Failures degrade to rule results with an issue flag; quality depends on running a ≥ 7B model on adequate hardware.
**Status:** accepted
