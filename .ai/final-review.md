# Final review — Examind (2026-09-22)

Everything in this file was decided and built autonomously under the blanket pre-approval given in chat
("Không dừng ở gate nào … Xong hết tất cả tôi review 1 lần"). Every gate was passed with `aidlc pass --by "Loc Tran"`
only after `aidlc check` succeeded; every ticket was closed with `aidlc done --no-review` after its recorded test run
exited 0. **Please review the sections below and tell me which assumptions or ADRs to change.**

## 1. What exists

| # | Feature | Gate | Tickets | What you can do |
| --- | --- | --- | --- | --- |
| 1 | `platform-foundation` | G5 | 20 | Org-code login, forced password change, super admin org CRUD, users + CSV/XLSX import, classes, Toán 6–12 topic tree (ltree) + tags, `QuestionView` |
| 2 | `exam-ingestion` | G5 | 18 | Upload .docx/.pdf/.png/.jpg → worker splits into questions (stem, options, answer, solution, images), OCR (Tesseract vie), AI model registry + per-upload model choice, AI fallback, topic suggestions |
| 3 | `question-review` | G5 | 14 | Auto-triage (≈0% flagged on the samples), trigram dedupe, keyboard review queue with source page, answer-key paste, bank search/edit/create/bulk, kNN topic learning |
| 4 | `exam-practice` | G5 | 15 | Exam builder (blueprint by topic subtree/tag), assignments, timed exam page with autosave, THPT-2025 scoring, results + solutions, essay grading, reports by topic level/tag/type/difficulty, heatmap |
| 5 | `adaptive-review` | G5 | 8 | Mastery per topic (EMA), "Tạo đề ôn tập", personal review exams for a class, suspect-answer-key audit |

Totals at close: **API 200 tests, web 84 tests passing**, `tsc` and `eslint` clean, `next build` OK. 75 tickets across 18 UoWs.
Every UoW has a demo evidence file (`.ai/features/*/07-demo-evidence.md`) with what was checked in a real browser vs by tests.

## 2. Run it

```bash
cp .env.example .env            # set APP_ENCRYPTION_KEY (command in the file) and change secrets
docker compose up -d --build --wait          # web + api + worker + postgres + minio + caddy
open http://localhost:8088/login
./scripts/verify.sh apps/api/tests apps/web/src   # all tests (API tests run inside the api image)
```

Optional local LLM: `docker compose --profile ai up -d ollama && docker compose exec ollama ollama pull qwen2.5:7b`.

Dev data currently in your local DB (change before exposing anything):

| Org code | Username | Password | Role |
| --- | --- | --- | --- |
| system | admin | admin123456 | super_admin |
| trungtama | admin | admin123456 | org_admin |
| trungtama | buivanchau | hocsinh123 | student (10A1) |

The other 29 imported students still have temporary passwords (reset them from "Người dùng").

## 3. Deviations from the chat plan (please confirm)

| Plan said | Built | Why |
| --- | --- | --- |
| LiteLLM | Own thin adapters for Ollama / OpenAI-compatible / Anthropic (`app/ingestion/llm.py`) | 3 protocols cover every free/paid option; far fewer dependencies on ARM (exam-ingestion ADR-03) |
| PaddleOCR or Surya | Tesseract `vie` by default, AI-vision OCR as an option | apt-installable on arm64; PaddleOCR wheels are weak on ARM (ADR-05) |
| Docling/marker for PDF | pdfplumber + pypdfium2 | no torch/model downloads; no AGPL (PyMuPDF) (ADR-04) |
| pgvector embeddings for dedupe + kNN | pg_trgm similarity on normalised text | no model needed; works for near-identical exam text (question-review ADR-01); pgvector extension is installed for a later upgrade |
| Redis queue | Postgres `jobs` table with SKIP LOCKED | one fewer service on a single VM (ADR-01) |
| Ports 8080 | Caddy on **8088**, dev Postgres 55442, MinIO 59100, API 58100 | 8080/55432/59000 were taken on your Mac by other stacks |
| BKT/IRT | Difficulty-weighted EMA mastery | too little data at the start; one table to swap later |

## 4. Not done / needs you

| Item | Status | What is needed |
| --- | --- | --- |
| Real exam files golden set | Only generated samples (`samples/exams/`) | 10–20 of your real .docx/.pdf/scans; I will add them to the golden tests and tune the splitter |
| Local LLM | **Done 2026-09-22**: native Ollama (Homebrew, Metal) with `qwen2.5:7b` on the M2 Pro; stack reaches it at `http://host.docker.internal:11434` (`OLLAMA_URL`, `LLM_TIMEOUT_SECONDS=180` in `.env`). AI-only split of `de-kho.docx`: 8/8 correct, ~4.7 s per question, 0 failures (1.5B model disabled) | On the Oracle VM (CPU only) expect it to be much slower — keep rule-based as the main path there |
| Oracle VM deployment | Documented in the plan; not executed | An Oracle account, a VM, and a domain (or use sslip.io) |
| Backup scripts (`pg_dump` + `mc mirror` cron) | Not written | Decide the backup target (R2 or your machine) |
| CI (GitHub Actions), Sentry | Not set up | A GitHub repo; a Sentry DSN (optional) |
| Google OAuth, printable exam export (.docx/.pdf, multiple versions), PWA | Post-MVP by plan | — |
| Legacy dev data | Questions parsed before later fixes keep old artefacts (e.g. `n⃗` glyph box in one PDF, docx + PDF copies both usable) | Re-parse those documents or reset the dev DB |

No ticket was ever `aidlc block`-ed.

## 5. Process record

- Review bypasses (`done --no-review`): 20 + 18 + 14 + 15 + 8 = **75** (every ticket; solo mode as agreed). Full trail: `./scripts/aidlc -d .ai/features/<slug> audit`.
- `aidlc flow` estimate bias is not meaningful here: tickets were started and closed by the same agent in minutes (estimates 31.5 d vs recorded ≈ 1.4 h).
- Demo findings that changed code (all recorded as ADRs): OCR-glued option labels, OCR flags blocking manual approval, shuffled options keeping original labels, PDF combining arrows, mastery backfill, small-model JSON drift.

## 6. Assumptions decided under pre-approval

Status in the registers is `confirmed` with the note "Accepted under blanket pre-approval … to confirm at final review". Change any row and I will re-open the affected feature (`aidlc reopen`).


### 2026092101-platform-foundation

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | Org code is 3–32 chars of `[a-z0-9-]`, stored lower-case, matched case-insensitively (`TrungtamA` == `trungtama`) | yes |
| A-02 | Username unique per org, case-insensitive, `[a-z0-9._-]` 3–64 chars; auto-generated from full name without diacritics when CSV leaves it blank (`nguyenvana`, then `nguyenvana2`) | yes |
| A-03 | Roles are exactly `super_admin`, `org_admin`, `teacher`, `student`; one role per user | yes |
| A-04 | super_admin lives in a reserved org `system` that cannot be edited, suspended or deleted | no |
| A-05 | Teachers may create students and reset student passwords, but not manage other teachers or admins | no |
| A-06 | Access token 15 min, refresh token 30 days, both httpOnly SameSite=Lax cookies; refresh tokens stored hashed and revoked on org suspend / password reset | yes |
| A-07 | Lockout: 5 failed logins for the same (org, username) within 15 min → locked 15 min; per-IP limit 30/min | no |
| A-08 | CSV columns: `full_name` (required), `username`, `role` (default student), `class`; UTF-8 with or without BOM; `.xlsx` also accepted; max 2000 rows | no |
| A-09 | Temp passwords are 10 chars from an unambiguous alphabet, returned once in a downloadable CSV and never retrievable again | no |
| A-10 | Topic tree is per organisation, seeded from a shared Toán 10–12 (GDPT 2018) template at org creation; nodes carry `level_kind` ∈ strand/topic/subtopic/type; max depth 5 | yes |
| A-11 | Subjects, grades (6–12) and semesters (HK1/HK2) are fixed seed data per org in this feature; editing them is out of scope | no |
| A-12 | Tags are per org with a group ∈ method/skill/source/custom; name unique per (org, group) | no |
| A-13 | Deleting a topic node with children or (later) questions is refused; merging moves children + references to the target | no |
| A-14 | UI language is Vietnamese only for MVP | no |
| A-15 | Org soft delete sets `deleted_at`, frees nothing, blocks login; hard delete allowed only when the org has no users other than its admins | no |
| A-16 | Seed super admin credentials come from env `SUPERADMIN_USERNAME`/`SUPERADMIN_PASSWORD` (dev default `admin` / `admin12345`) and must be changed on first login | no |

### 2026092201-exam-ingestion

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | Vietnamese exams mark questions with `Câu N` (optionally `Câu N.`, `Câu N:`, `Câu N (0,25 điểm)`), options with `A.`–`D.` (also `A)`), true/false statements with `a)`–`d)` | yes |
| A-02 | Answers appear as one of: inline `Đáp án: C` / `Chọn C`; an answer-key table/list at the end (`1.A 2.C`, or a table); or the correct option underlined/bold/coloured in Word | yes |
| A-03 | Solutions appear either right after each question (`Lời giải`, `Hướng dẫn giải`, `Giải`) or in a trailing section whose items restart numbering at `Câu 1` | yes |
| A-04 | THPT 2025 structure: `PHẦN I` MCQ, `PHẦN II` true/false (4 statements), `PHẦN III` short answer; older exams are all-MCQ; essays exist in school exams (`Bài N`) | no |
| A-05 | Docx equations are OMML (Word 2007+); Pandoc converts them to TeX. MathType objects stay images | no |
| A-06 | Scans are printed text; Tesseract `vie` gives usable text; formulas in scans are imperfect and flagged low-confidence | no |
| A-07 | Max upload 30 MB, 60 pages; .docx, .pdf, .png, .jpg accepted; .doc (binary) rejected with a hint to save as .docx | no |
| A-08 | Same file (sha256) uploaded twice in one org returns the existing document instead of parsing again | no |
| A-09 | Worker processes at most `INGEST_CONCURRENCY` (default 1) jobs; a job retries up to 2 times with backoff; a stuck job (locked > 15 min) is re-queued | no |
| A-10 | LLM providers: `ollama` (native API), `openai` (any OpenAI-compatible server incl. LM Studio, vLLM, Gemini's OpenAI endpoint), `anthropic`; API keys encrypted at rest with a key from env `APP_ENCRYPTION_KEY` | yes |
| A-11 | System-wide models (organization_id NULL) are managed by super_admin and visible to every org; org models by org_admin | no |
| A-12 | Parsed questions are stored as `status = draft` with `confidence` 0–1 and `issues[]`; approval happens in `question-review` | yes |
| A-13 | Topic suggestion in this feature: keyword match against leaf topic names (always) + LLM choice among leaf topics when a text model is configured; stored as `question_topics.source = 'auto'` with a score | no |
| A-14 | Re-parsing a document replaces its draft questions; questions already approved are never deleted by a re-parse | yes |

### 2026092202-question-review

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | Statuses: `draft` (legacy) → at ingestion `auto_approved` or `needs_review`; teacher actions give `approved` / `rejected`; `duplicate` for near-duplicates. `auto_approved` and `approved` are both usable in exams | yes |
| A-02 | Auto-approve needs confidence ≥ org threshold (default 0.85) AND an answer (except essays) AND no blocking issue (`thiếu phương án`, `thiếu đáp án`, `đáp án không khớp…`, `OCR`, `AI không phản hồi`, `không nhận ra phương án`) | yes |
| A-03 | Near-duplicate = same org, same type, trigram similarity of normalised stem+options ≥ 0.9 against a usable question; the new one becomes `duplicate` with `duplicate_of` | no |
| A-04 | Source view: PDFs/scans show the rendered source page next to the question; Word files show no page image | no |
| A-05 | Keyboard map: Enter approve+next, 1–4 set MCQ answer A–D (a–d toggles for true/false), T topic search, E edit, X reject, J/K next/previous, S skip, ? help | no |
| A-06 | Answer-key paste accepts "1A 2C 3B", "1.A, 2.C", "1-A", or a column of letters; applies to MCQ by number in the document (part-aware with "PHẦN I:" prefixes) | no |
| A-07 | Spot check: 5% (min 1) of auto-approved questions per document are queued as "Kiểm tra ngẫu nhiên"; if ≥ 2 of the last 20 spot checks in the org were rejected or edited, the org threshold rises by 0.05 (max 0.95) | no |
| A-08 | kNN topic suggestion: when keyword score is weak (< 0.6) the primary topic of the most similar approved question (trigram ≥ 0.35) is suggested with source `knn` | no |
| A-09 | Review assignment is per document (`assigned_to`), optional; queue filter "Của tôi" | no |
| A-10 | Bank search: text (unaccented, trigram), subject, grade, semester, exam kind, topic subtree, tags (any), type, difficulty, status, source document; page size 20 | no |
| A-11 | Teachers edit any question of their org; students never see the bank | no |

### 2026092203-exam-practice

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | An exam is an ordered list of questions grouped in sections by type (Phần I MCQ, II true/false, III short answer, IV essay); points per question default by type and can be overridden per exam | yes |
| A-02 | True/false partial credit (THPT 2025): 1 correct statement 0.1, 2 → 0.25, 3 → 0.5, 4 → 1 × question points; 0 correct → 0 | yes |
| A-03 | Short answers compare after normalisation: trim, comma = dot decimal, fractions a/b evaluated, numeric equality within 1e-9; otherwise case-insensitive text equality without accents | no |
| A-04 | Blueprint rows: {topic_id (subtree) or tag_id, type, difficulty?, count}; questions drawn from usable questions at random with a seed; the same question never appears twice; rows that cannot be filled report the shortfall | yes |
| A-05 | Assignment: exam → one or more classes and/or students, open_at, close_at, duration (minutes), max_attempts (default 1), shuffle questions/options, results policy (after_submit / after_close / never) | yes |
| A-06 | Attempt deadline = min(started_at + duration, close_at) + 30 s grace; after it the attempt is finalised with the saved answers | yes |
| A-07 | Answers autosave on every change (debounced 500 ms client-side); the server stores the latest value per question | no |
| A-08 | Essays are graded by teachers (score 0..points + comment); an attempt with ungraded essays shows "Đang chấm" for those points | no |
| A-09 | Stats are computed from `answer_facts` (one row per graded answer with the question's primary topic path, tag ids, type, difficulty, points, max) and roll up topic levels with ltree | yes |
| A-10 | Students see only their own attempts and assignments of their classes; teachers see everything in the org | no |
| A-11 | Questions used by an exam cannot be hard-deleted (bank delete → 409); editing a question after an exam was taken does not change past answers' grades (answers store the graded snapshot) | no |
| A-12 | Tab switches during an attempt are counted and shown to the teacher; no blocking | no |

### 2026092204-adaptive-review

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | Mastery per (student, leaf topic) = exponential moving average of answer correctness with α = 0.3, where each answer's weight grows with difficulty (nb 0.8, th 1.0, vd 1.2, vdc 1.4); starts at 0.5 with the first answer | yes |
| A-02 | Parents' mastery = answered-weighted average of descendants (computed at read time) | no |
| A-03 | Review exam default 20 questions: 60% from the 3 weakest leaf topics (mastery < 0.8, ≥ 1 answer), 30% from medium topics (0.5–0.8), 10% re-ask of questions answered wrong ≥ 24 h ago; fill from weakest topics' neighbours when short | yes |
| A-04 | Target difficulty by mastery: < 0.4 → nb/th, 0.4–0.7 → th/vd, > 0.7 → vd/vdc; questions without difficulty count as th | no |
| A-05 | Questions answered correctly in the last 7 days are excluded from new review exams; flagged/non-usable questions are always excluded | no |
| A-06 | Student self-practice: untimed-in-practice but capped at 60 minutes, results shown immediately, no attempt limit; stored as attempts without assignment | no |
| A-07 | Teacher "đề ôn cá nhân" for a class creates one adaptive exam per student and one assignment per student (window + duration from the dialog) | yes |
| A-08 | Suspect key rule: a MCQ with ≥ 10 graded answers where the top-quartile students (by attempt score) chose one other option at least 60% of the time → status `flagged` with issue "Nghi sai đáp án" and the evidence stored; also flagged when overall correctness < 15% with ≥ 20 answers | no |
| A-09 | Detection runs in the worker every 10 minutes and on demand; flagged questions reappear in the review queue of their source document (or a "Câu bị gắn cờ" list for manual questions) | no |

## 7. Architecture decisions (ADRs)

- **2026092101-platform-foundation**: ADR-01 — Self-host everything in one Docker Compose; ADR-02 — Org-code login with per-org usernames; ADR-03 — Tenancy enforced in the service layer; ADR-04 — Topics as `ltree` materialised paths; ADR-05 — Cookie JWT through a same-origin reverse proxy; ADR-06 — Web tests outside route-group folders; ADR-07 — Raster images only; SVG uploads rejected; ADR-08 — Dev ports and compose override
- **2026092201-exam-ingestion**: ADR-01 — Postgres job queue; ADR-02 — Canonical line stream between extractors and the splitter; ADR-03 — Thin LLM adapters instead of LiteLLM; ADR-04 — pdfplumber + pypdfium2 for PDFs; ADR-05 — Tesseract as default OCR, AI vision optional; ADR-06 — API tests run inside the api image; ADR-07 — Encrypted provider keys; ADR-08 — Pillow allowed in the API image; ADR-09 — Bounded LLM generations and schema-constrained output
- **2026092202-question-review**: ADR-01 — pg_trgm for dedupe, kNN and search; ADR-02 — One quality module for ingestion and editing; ADR-03 — Status column + append-only review events; ADR-04 — Keyboard-first single-question queue; ADR-05 — Two blocking levels: auto-approval vs manual approval; ADR-06 — OCR-tolerant option labels
- **2026092203-exam-practice**: ADR-01 — answer_facts written at grading time; ADR-02 — Server-authoritative deadlines with lazy + swept closing; ADR-03 — Grading snapshot per answer; ADR-04 — Pure scoring module; ADR-05 — Grouped sidebar navigation; ADR-06 — Shuffled options are relabelled per attempt
- **2026092204-adaptive-review**: ADR-01 — Difficulty-weighted EMA mastery on leaf topics; ADR-02 — Adaptive exams are ordinary exams; ADR-03 — Top-quartile key audit

## 8. Where things are

| Path | Content |
| --- | --- |
| `.ai/roadmap.md`, `.ai/architecture.md` | Feature order, target layout (verified_by pre-approval) |
| `.ai/features/<slug>/00-03*.md` | Intent, assumptions, requirements (Given/When/Then), logical design + ADRs |
| `.ai/features/<slug>/04-units-of-work/` | UoWs with demo scripts and tickets (touches, tests, done-when) |
| `.ai/features/<slug>/05-ticket-graph.md`, `06-traceability.md` | Generated waves/critical path and AC → ticket → test matrices |
| `.ai/features/<slug>/07-demo-evidence.md` | What was demonstrated and how |
| `apps/api`, `apps/web`, `docker-compose*.yml`, `infra/`, `samples/` | Code, stack, Caddy, sample exams with ground truth |


## 9. Golden set with rule + AI fallback (qwen2.5:7b, Mac native) — 2026-09-22

`scripts/golden_live.py` (runs against the live stack, logs in as trungtama/admin).

| File | rule | rule_ai | AI calls | Needs review rule → rule_ai | Time rule_ai |
| --- | --- | --- | --- | --- | --- |
| de-mau-toan10.docx | 40/40 | 40/40 | 0 split, 2 tag | 0 → 0 | 8.6 s |
| de-mau-toan10.pdf | 40/40 | 40/40 | 0 split, 3 tag | 0 → 0 | 7.7 s |
| de-thpt2025-toan.docx | 22/22 | 22/22 | 0 split, 3 tag | 0 → 0 | 4.9 s |
| de-2cot.pdf | 10/10 | 10/10 | 0 split, 1 tag | 0 → 0 | 1.9 s |
| de-kho.docx | **3/8** | **8/8** | 5 split | 5 → 0 | 25 s |
| de-scan.pdf (numbers found) | 10/10 | 10/10 | 10 split | 8 → 6 | 68 s |
| de-scan.png (numbers found) | 5/5 | 5/5 | 5 split | 4 → 4 (Q5 answer now filled) | 33 s |

- The AI is only called for low-confidence blocks, so clean files cost nothing extra; the remaining scan reviews are the deliberate `OCR` needs-eyes flag.
- Topic (de-mau-toan10, 40 labelled), first run: exact node 30/40; one wrong AI pick (Q26 "A ∩ B" → "Đại số tổ hợp") because the AI result always overrode keywords.
- **Fixed 2026-09-22** (`topic_suggest.py`): keyword/kNN first; the model is only asked about weak matches, and over a weak keyword topic it may only refine to a descendant (never a parent or another branch); a returned `name` is checked against the index; single math symbols (∩ ∪ ⊂) count as cues, so PDF text scores like docx.
  Re-run: docx and PDF both **40/40 in the right branch** (30 exact node, 10 a more specific child), AI tag calls 0 on clean files, splitting unchanged (all 7 files 100%). Questions tagged before the fix keep their old topic — re-parse or fix them in the bank.
