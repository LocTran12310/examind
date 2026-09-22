# Demo evidence — architecture-refactor

## UOW-01 foundation + Tags (2026-09-22)
- `lint-imports`: 4 contracts kept (module layers, pure domain, pure application, shared kernel);
  `tests/test_architecture.py` also checks that modules only import each other's `application`.
- API suite 316 passed (+1 skipped: official set needs EXAMIN_DIR); new `test_errors.py`, `test_search_contract.py`,
  `tests/unit/test_tag_handlers.py` (handlers against in-memory ports, no database).
- Live: `POST /api/tags/search {filters:{name:{operator:"+",value:"sở"}},limit:3}` → `{data,total,page,limit}`;
  `sort:[{field:"nope"}]` → 422 `{code:"bad_sort", message, details:{fields, requestId}}`, same id in `X-Request-Id`.
- Live Tags page: list via `POST /tags/search`; "Thêm tag" → dialog closes, table shows 20 rows without a reload key;
  delete → 19 rows. Bank page pickers load tags through the same query hook.
- Web 149 tests, tsc and eslint (boundary rules) clean.

## UOW-02 topics, taxonomy and the academic context (2026-09-22)
- API modules `taxonomy` (subjects, semesters, topics tree) and `academic` (school years + terms + rollover, classes +
  members, structure, student record); `lint-imports` 4 contracts kept with `app.modules.academic` added;
  `test_architecture.py` green (identity columns read through lightweight tables, no module imports the old models).
- Endpoints moved to search (old GET lists answer 405): `GET /school-years` → `POST /school-years/search`,
  `GET /classes` → `POST /classes/search` (+ `school_year_id`, `grade_id`), `GET /school-levels` → `POST /school-levels/search`,
  `GET /grades` → `POST /grades/search` (+ `school_level_id`). Unchanged paths and JSON: `/taxonomy`, `/topics` (tree) and
  its create/rename/move/merge/delete, `/structure`, `/school-years/{id}` + activate/close/reopen + rollover preview/commit,
  class CRUD + members, `/students/{id}/record`. 34 routes now served by handlers (7 taxonomy, 27 academic).
- API suite 325 passed (+1 skipped: official set needs EXAMIN_DIR): new `tests/unit/test_topic_handlers.py` and
  `tests/unit/test_academic_handlers.py` (in-memory ports), `tests/test_academic_search.py` (typed filters, bad_sort /
  bad_filter, limit 1000, old GETs gone); demo script covered over HTTP by `test_topics_api.py` (add, rename, move, merge,
  delete), `test_school_years.py` + `test_rollover.py` (create, terms, activate, rollover), `test_classes_api.py` (members).
- Web: Topics, Structure, School years, Rollover, Classes, Class detail and Student record run on services → query hooks →
  page hooks → page components (routes one line); the header year lives in `stores/common/year.store.ts`
  (`examind.year.<org>`), `useYear()` kept. Users, exam and report screens read classes through `useClassOptionsQuery`.
  Web 152 tests, tsc and eslint clean. Not re-run on the live stack (running containers still on the previous image).

## UOW-03 identity: sessions, users, organisations (2026-09-22)
- API module `identity` (4 layers): sessions (login with lockout and IP throttle, refresh rotation with replay revocation, logout,
  switch-org, change password, `/auth/me`, `/me/orgs`), users of the org (CRUD, reset password, link/unlink, CSV/XLSX import),
  organisations and memberships (platform admin). Argon2 hashing, JWT and refresh-token secrets, the rate limiter and the spreadsheet
  reader are adapters behind ports; the class directory (academic application API) and the org seeder are wired by `main.py`.
  `schema/identity.py` now holds the only Table objects of `organizations`, `users`, `organization_members`, `refresh_tokens`;
  `app/models/{user,org}.py`, `app/deps.py`, `services/{auth,membership,users}.py`, `core/{security,passwords}.py` are re-export shims.
  The actor resolver is `identity.interface.deps.actor_from_request`; `OrgScope`/`org_scope`/`current_user`/`require_role` wrap it.
  `lint-imports` 4 contracts kept with `app.modules.identity` added; `test_architecture.py` green.
- Endpoints moved to search (old GET lists answer 405/404): `GET /users` → `POST /users/search` (+ `class_id`),
  `GET /admin/orgs` → `POST /admin/orgs/search` (+ `include_deleted`), `GET /admin/users` → `POST /admin/users/search`,
  `GET /admin/orgs/{id}/members` → `POST /admin/orgs/{id}/members/search`,
  `GET /admin/users/{id}/memberships` → `POST /admin/users/{id}/memberships/search`. Every other identity path and JSON body unchanged
  (login error bodies identical apart from `requestId`, cookies and JWT unchanged).
- API suite 340 passed (+1 skipped: official set needs EXAMIN_DIR): new `tests/unit/test_identity_handlers.py` (15 handler tests on
  in-memory ports) and `tests/test_identity_search.py`; existing tests changed only for the new URLs/shapes.
- Web: shell (AppShell, AppSidebar, OrgSwitcher, UserMenu, YearSwitcher, SessionRecovery) in `components/layout/`; login, change password,
  users (+ class members table), import wizard, admin orgs/accounts/memberships on services → query hooks → page hooks → page components.
  Switching organisation calls the API, clears the query cache (`useSwitchOrgMutation`), `router.push` + `router.refresh` — no full reload.
  Web 153 tests, tsc and eslint clean.
- Live (`docker compose up -d --build api worker web`, http://localhost:8088, trungtama/admin): login 200 (org_admin, trungtama);
  wrong password 401 `invalid_credentials` with the same message; `/auth/me` 200; `POST /users/search` role=student → `{data,total,page,limit}`
  total 30; `GET /users` 405; `/me/orgs` 200; `POST /auth/switch-org` 200; `/auth/refresh` 204; `/login` page 200.

## UOW-04 question bank and review (2026-09-22)
- API module `bank` (4 layers): the Question aggregate (dataclass on `shared/infrastructure/schema/bank.py`, the only Table objects of
  `questions`, `question_topics`, `question_tags`, `review_events`) with create, update, delete (in-use guard, duplicates released), bulk,
  review actions (approve / reject / restore / skip, spot_ok / spot_fail, threshold feedback), answer key, approve-confident, reviewer
  assignment, key audit and ingestion triage (near-duplicates) through handlers. Quality rules, search text, answer-key parsing, review
  and key-audit rules are pure domain services. Topic / tag / subject checks go through the new `taxonomy/application/api.py`
  (`TaxonomyApi`), the reviewer check through `IdentityApi.role_in` + new `is_super`; both are wired in `main.py`
  (`register_taxonomy`, `register_staff_directory`). Source documents, org threshold and submitted answers are read through Core adapters.
  `lint-imports` 4 contracts kept with `app.modules.bank` added; `test_architecture.py` green.
- Old layout kept working through shims: `app/models/{question,review}.py` and `QuestionTopic`/`QuestionTag` in `models/document.py`
  re-export the bank dataclasses; `services/{bank,triage,key_audit,answer_key,question_quality,search_text}.py` delegate
  (`bank.search_ids`, `IN_USE_CHECKS`, `release_duplicates_of`, `triage_hook`, `audit`); `schemas/questions.py` and the question part of
  `schemas/documents.py` re-export the bank schemas; `routers/documents.parsed_many` uses the bank presenter. `routers/{questions,review}.py`,
  `services/review.py`, `schemas/review.py` removed. `strip_markup` / `PART_RE` / `ROMAN` moved to `shared/domain/text.py` (ingestion re-imports).
- Endpoints moved to search (old GETs answer 405): `GET /questions` → `POST /questions/search` (bank params at the top of the body,
  `topic_ids` / `tag_ids` arrays, `limit` ≤ 1000; typed filters stem, created_at, updated_at, number, grade), `GET /questions/facets` →
  `POST /questions/facets` (same body), `GET /review/documents` → `POST /review/documents/search` (+ `mine`),
  `GET /review/flagged` → `POST /review/flagged/search`. Every other question / review path and JSON body unchanged.
- API suite 351 passed (+1 skipped: official set needs EXAMIN_DIR); official golden set with EXAMIN_DIR 1 passed. New
  `tests/unit/test_bank_handlers.py` (11 handler tests on in-memory ports); existing tests changed only for the new URLs/shapes.
  `test_triage.py::test_pdf_copy_of_docx_is_marked_duplicate` failed once on a re-run (two original questions with the same text tie on
  similarity; the duplicate query is unchanged from before) and passed on the next run.
- Web: bank list (SubjectTabs, FilterSheet, FilterChips, facets, BulkBar), question detail / new, review list and review document (queue,
  editor, answer key, approve-confident) on `question.service` / `review.service` → `use-query-question` / `use-query-review` → page hooks →
  page components; routes one line. Subject per org in `stores/common/bank-subject.store.ts` (same `examind.bank.subject.<org>` key).
  QuestionView, Markdown, MarkdownEditor, TopicPicker, QuestionForm, QuestionFields moved to `components/common/`. Exam builder search box
  and the dev preview use the query hooks (lint exception line). Web 154 tests, tsc and eslint clean.
- Live (`docker compose up -d --build api worker web`, http://localhost:8088, trungtama/admin): `POST /questions/search {status:"all"}` total
  397 (396 from the 18 documents + the demo question), usable 377; `POST /review/documents/search` 18 documents, 396 questions;
  Toán 356 → + one topic subtree 43 → + a source tag 2 (e.g. "Hoán vị, chỉnh hợp, tổ hợp", tag of Trường THPT Thuận Thành); facets for the three filters types {mcq 1, short_answer 1};
  queue of a document 1, flagged 0; `GET /questions` 405.

## UOW-05 documents and ingestion (2026-09-22)
- API module `ingestion` (4 layers). Pure rules moved unchanged to `domain/services/`: `mtef`, `splitter`, `lines`, `header`
  (`apply(doc, lines, subjects)` no longer queries), `docx_ast` (the Pandoc AST walker and MathType token swap), `ocr_text` (Tesseract TSV),
  `ai_parse` (prompts, JSON schema, model drift, `parse_json`), `topic_rules` (cues, name-over-index, refine-only), `documents` (kinds, meta,
  names, duplicate identity), `processing` (upload > org > system config), `ai_models` (registry checks). I/O behind ports
  (`domain/ports.py`) in `infrastructure/adapters/`: `pandoc` (DocxReader), `pdf` (pdfplumber reader, pdfium page renderer), `tesseract`
  (Scanner), `vector_images` (LibreOffice), `llm` (httpx ChatModels), `crypto` (Fernet KeyCipher, was `core/crypto.py`), `storage` (S3),
  `settings` (organizations.settings), `taxonomy` (Core reads + the taxonomy API for source tags), `bank` (the bank API).
  The pipeline is `application/commands/ingest_document.py` (extract → header → split → AI stage → persist → triage → topic suggestion, same
  order, same two commits, same step log) with the stages as application services (`stages/extract|ai_split|topic_suggest`); the stage
  registries (`EXTRACTORS`, `POST_SPLIT`, `POST_PERSIST`, `ocr.PROVIDERS`) are gone, the handler calls them explicitly.
- Cross-module calls through `application/api.py` only, wired in `main.py` and in the worker (`app/worker/handlers.py`): the bank API gained
  `remove_document_questions`, `kept_positions`, `add_parsed`, `triage_ids`, `nearest_topic`, `suggest_topic`, `follow_document`,
  `document_questions`; the taxonomy API gained `source_tag`; `POST /documents/{id}/exam` calls the exam service (assessment, not moved yet)
  through `ExamServiceDrafts` registered by `main.py`. `GET /documents/{id}/questions` is served by the bank router (the bank owns questions).
  The question quality rules moved to `shared/domain/question_quality.py` and `same_short_answer` to `shared/domain/answers.py` (both used
  by ingestion's splitter and by bank / assessment; old paths re-export). Jobs: `shared/infrastructure/schema/jobs.py` + `sql_jobs.SqlJobQueue`
  (enqueue in the command's transaction); the worker keeps its queue (SKIP LOCKED claim, retries, stale recovery), `Job` is a dataclass
  mapped on that table; each job type calls an application command (`IngestDocument`, `MarkIngestFailed`).
  `schema/ingestion.py` holds the only Table objects of `source_documents`, `assets`, `ai_models`; `app/models/{document,asset,ai_model,job}.py`,
  `services/{documents,assets}.py`, `schemas/documents.py`, `core/images.py` (sniff → `shared/domain/images.py`) are re-export shims;
  `app/ingestion/`, `routers/{documents,assets,ai_models,org_settings}.py`, `services/{ai_models,ingestion_settings}.py`, `schemas/ai_models.py`
  removed. `lint-imports` 4 contracts kept with `app.modules.ingestion` added; `test_architecture.py` green.
- Endpoints moved to search (old GETs answer 405): `GET /documents` → `POST /documents/search` (filters filename, source_name · status, mime ·
  question_count · created_at; `q` over filename and source), `GET /ai-models` → `POST /ai-models/search` (name, model · provider · enabled,
  is_free). Every other documents / assets / AI models / `org/settings/ingestion` path and JSON body unchanged.
- Flaky `test_triage.py::test_pdf_copy_of_docx_is_marked_duplicate`: the duplicate-candidate query (bank `SqlDuplicateFinder`) now breaks
  similarity ties by the same part/number, then created_at, then id (a strictly more similar candidate still wins). 5 runs in a row passed.
- API suite 368 passed (+1 skipped: official set needs EXAMIN_DIR; 351 before the new tests); new `tests/unit/test_ingestion_handlers.py`
  (15 handler tests on in-memory ports: upload / duplicates / replace / busy, re-parse, meta + source tag, delete, the pipeline incl. header
  detection, kept positions and a teacher-facing failure, crash hook, document image store, AI model key encryption and rights, processing
  defaults) and `tests/test_ingestion_search.py` (typed filters, sort, paging, bad_filter / bad_sort, old GETs 405).
- Golden, official set (EXAMIN_DIR, `tests/test_golden_official.py`): 18 documents → 396/396 questions, 393 with answers (393/393 right),
  386/386 solutions, 0 pictures lost. Live (`scripts/golden_live.py`, EXAMIN_DIR mode, on_duplicate=replace through the worker): 18 documents
  parsed, 396/396 found, 386 solutions, 7,887 formulas, 31 vector figures, 23.1 s of pipeline time.
- Web: documents list (polls every 2 s while a document is queued/processing), document detail, UploadForm (browser SHA-256,
  `POST /documents/check`, per-file skip / replace / keep both), DocumentMetaFields, ProcessingConfig, parsed question cards, AI models page and
  ingestion settings page on `document.service` / `ai-model.service` / `ingestion-settings.service` → `use-query-document` /
  `use-query-ai-model` / `use-query-ingestion-settings` → page hooks → page components; routes one line; `components/documents/*` and
  `components/ai/*` removed. Web 154 tests, tsc and eslint clean.
- Live (`docker compose up -d --build api worker web`, http://localhost:8088, trungtama/admin): `POST /documents/search` total 18 (all parsed);
  `GET /documents` 405; `POST /documents/check` with the SHA-256 of `07. TRƯỜNG THCS -THPT NGUYỄN KHUYẾN…docx` → `same_file` (22 questions);
  `POST /ai-models/search` total 2; `GET /ai-models` 405; `GET /org/settings/ingestion` 200; worker heartbeat fresh, the 18 re-parse jobs
  claimed and `done`. After the re-parse the 18 documents report 331 new questions: 65 questions used in exams survive a re-parse and are
  not recounted (unchanged rule, A-14); the bank still holds 396 questions of the 18 documents.
- Demo script: (1) re-uploading the 18 files is reported as duplicates (`/documents/check` → `same_file`; upload `skip` returns the
  existing document, `replace` re-parses it — the live golden run above); (2) golden numbers above; (3) exam from a document over HTTP in
  `test_exam_from_document.py` (draft in PHẦN / Câu order, 422 before approval, kept across a re-parse) — not repeated on the live data.

## UOW-06 exams, assignments and attempts (2026-09-22)
- API module `assessment` (4 layers): dataclasses `Exam`, `ExamQuestion`, `Assignment`, `AssignmentTarget`, `Attempt`, `AttemptAnswer`,
  `AnswerFact` mapped on `shared/infrastructure/schema/assessment.py` (the only Table objects of `exams`, `exam_questions`, `assignments`,
  `assignment_targets`, `attempts`, `attempt_answers`, `answer_facts`). Pure rules in `domain/services/`: `scoring` (THPT 2025 scale, moved
  unchanged), `exam_rules` (settings, sections and numbering, blueprint rows, PHẦN / Câu order), `assignment_rules` (window, attempt limit,
  deadline, results visibility), `attempt_rules` (question / option order, A–D relabelling, answer checks, grace, grading on submit,
  essay grading). Handlers: 17 commands (exam create / update / delete, blueprint, add / remove / swap / reorder / points, exam from a
  document, assignment create / update / delete, start, save answer, submit, tab switch, essay grade, sweep) and 9 queries (exam and
  assignment search, exam, exam questions, assignment, student home, runner view, result, assignment report — moved here from the old
  stats service). `Grading` (application service) writes one answer fact per graded answer with the school-year snapshot and reports it,
  in grading order, to a `FactListener`.
- Cross-module calls through `application/api.py` only, wired in `main.py` and the worker (`app/worker/handlers.py`): the bank API gained
  `questions_of`, `of_document`, `pool`, `classification`; the academic API `class_names`, `members_of`, `classes_of`; the identity API
  `active_member_ids`; the taxonomy's `subject_exists` is reused. Ingestion's `ExamDrafts` now calls `AssessmentApi.exam_from_document`
  (the port receives the document's filename, status and meta); `ExamServiceDrafts` is gone. The bank's in-use check asks
  `AssessmentApi.question_in_use`. Analytics (old layout) keeps the topic mastery through `services/mastery.MasteryFactListener`; the
  worker's sweep calls `AssessmentApi.sweep_expired`. `lint-imports` 4 contracts kept with `app.modules.assessment` added;
  `test_architecture.py` green.
- Old layout kept working: `app/models/exam.py` re-exports the dataclasses; `services/scoring.py` re-exports the domain scoring,
  `services/exams.points_for`, `services/assignments.new_attempt` (personal practice) and `services/attempts.sweep_expired` are thin
  wrappers; `routers/{exams,assignments,attempts,presenters}.py`, `schemas/{exams,assignments}.py` removed; `services/stats.py` lost
  the assignment report.
- Endpoints moved to search (old GETs answer 405): `GET /exams` → `POST /exams/search` (title · grade · source · subject_id · created_at;
  sort also question_count, total_points; adaptive exams left out), `GET /exams/{id}/questions` → `POST /exams/{id}/questions/search`
  (stem · type, section · position, points), `GET /assignments` → `POST /assignments/search` (title · exam_id · open_at, close_at ·
  duration_minutes). Every other exam / assignment / attempt path and JSON body unchanged, including `/me/assignments` (plain list),
  `/assignments/{id}/report` (now served by assessment), `PUT /exams/{id}/order`, `X-Server-Time`.
- API suite 392 passed (+1 skipped: official set needs EXAMIN_DIR; 368 before): new `tests/unit/test_assessment_handlers.py` (21 tests on
  in-memory ports: THPT partial credit, blueprint seed / shortfalls, frozen exams, exam from a document, assignment validation, start
  window / target / attempts left / deadline capped by close, results policy, shuffle inside sections, A–D relabelling, grading + facts
  in order, essay grading, empty essay, lazy close + sweep dated at the deadline, hidden results) and `tests/test_assessment_search.py`
  (typed filters, sort, paging, bad_filter / bad_sort, old GETs 405); existing tests changed only for the new URLs/shapes.
- Web: exams list (server table, title → preview dialog fetched on click, row → questions table), exam detail (BlueprintEditor,
  ExamQuestions draft ordering, ExamQuestionsTable, preview, points by type, bank search box, AssignDialog, the exam's assignments),
  assignment report, student home, exam runner, result view and essay grader on `exam.service` / `assignment.service` /
  `attempt.service` → `use-query-exam` / `use-query-assignment` / `use-query-attempt` → page hooks → page components; routes one line;
  `components/exams/*` and `components/reports/AssignmentReport.tsx` removed; `Bar` → `components/common/ScoreBar`, `AnswerInput` →
  `components/common/AnswerInput`. The resizable splits (MasterDetail, StructureSplit) no longer read `localStorage` during server
  rendering (`/org/exams` and `/org/classes` answered 500 on the live stack). Web 166 tests, tsc and eslint clean.
- Live (`docker compose up -d --build api worker web`, http://localhost:8088, trungtama/admin, read-only): `POST /exams/search` total 3
  (the three exams from documents, 22 questions each); `POST /exams/{id}/questions/search` total 22 (positions 1.., section I, 0.25);
  `GET /exams/{id}` 200; `POST /assignments/search` total 2 (class 10A1, 1 student each), filtered by exam 1; `GET /assignments/{id}/report`
  1 student, 22 questions; `GET /exams`, `GET /assignments`, `GET /exams/{id}/questions` 405; pages `/org/exams`, `/org/exams/{id}`,
  `/org/assignments/{id}`, `/home` 200; worker healthy.
- Demo script: (1) matrix, order, preview over HTTP in `test_exams_api.py` (blueprint with shortfalls, manual edits, points, `PUT /order`,
  swap) and the web tests; (2) assign, take, result, essay grading in `test_assignments_api.py`, `test_attempts_api.py`,
  `test_results_api.py` — not repeated on the live data (no live exam, assignment or attempt was created or changed).
