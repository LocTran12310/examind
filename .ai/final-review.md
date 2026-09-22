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

## 10. F6 `ui-shadcn-shell` + F7 `school-structure-multi-org` (2026-09-22)

Approved in chat after the MVP review ("Khoan, quay lại với business logic, UI, thao tác" + back-office screenshots). Same rules: gates passed as Loc Tran, tickets `done --no-review` with recorded test runs.

**What changed**
- **UI on shadcn/ui** (radix base, Nova preset, lucide icons). `components/ui/` holds only CLI-generated files — the old barrel is gone and ESLint forbids importing it. App composites live in `components/app/*` (FormField on shadcn Field, FormDialog, ConfirmDialog, OptionSelect, ToneBadge, Panel, OrgSwitcher, UserMenu, ThemeToggle).
- **Light / dark / system theme**, navy sidebar that collapses to icons (sheet on phones), header with breadcrumb + **[Tổ chức] | theme | avatar menu** on the right.
- **One DataTable for every list**: navy toolbar (Thêm mới / Sửa / Xóa with confirm / Nạp + screen actions), search row under the headers, server-side filter/sort/paging, state in the URL (links and Back work), "Chi tiết" panel under the table for classes → học sinh and exams → câu hỏi. 369 360 users: ≤ 212 ms per page.
- **Cơ cấu trường** `/org/structure`: Cấp học › Khối › Lớp › Học sinh tree with counts + the table for the selected node. New orgs get THCS 6–9 and THPT 10–12; everything is editable per org, deletes are refused while children exist.
- **One account, several organisations**: `organization_members` (role per org), header selector switches org (super admin sees all orgs and works inside as org admin), "Thêm tài khoản có sẵn" / "Gỡ khỏi tổ chức" on Người dùng, "Vào tổ chức" on the admin org list. Login stays *org code (home) + username + password* and reopens the last org.

**Deviations from the approved plan (please confirm)**
| Plan said | Built | Why |
| --- | --- | --- |
| shadcn Select everywhere | shadcn `NativeSelect` in dense repeated form rows (answer key per option, blueprint rows, upload metadata); Radix `Select` for filters, toolbars and single fields | ADR-05 F6 — both are shadcn components; native keeps mobile/keyboard behaviour where rows repeat |
| TanStack Table (latest) | pinned `@tanstack/react-table@^8` | v9 changed the API; shadcn's data-table guide is v8 (ADR-06 F6) |
| Org detail "Thành viên" tab | "Vào tổ chức" + the normal Người dùng page | A-12 F7 — one place to manage members |
| — | Toasts bottom-right | Top-right covered the org selector |

**Dev data added for the demo**: org `ttb` (admin / admin123456), teacher `ttb / gvlan / giaovien123` linked to Trung tâm A as Giáo viên, class 10A3.

**Tests at close**: API 229 passed, web 110 passed; `tsc`, `eslint`, `next build` clean. Evidence: `.ai/features/2026092205-ui-shadcn-shell/07-demo-evidence.md`, `.ai/features/2026092206-school-structure-multi-org/07-demo-evidence.md`.

**Known limits / not done**
- Several campuses under one org, shared login by email/SSO, moving question banks between orgs (out of scope in F7).
- The system org also received THCS/THPT rows from the migration backfill (unused, harmless).
- "Nhập học sinh từ file" on the structure page opens the existing import screen; it does not preselect the class.


### Assumptions — 2026092205-ui-shadcn-shell

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | shadcn style new-york, base colour neutral, brand blue as `--primary`; font Be Vietnam Pro kept | no |
| A-02 | Theme default follows the OS; the choice (light/dark/system) is stored per browser by next-themes | no |
| A-03 | Table toolbar actions per screen: Thêm mới, Sửa (1 selected), Xóa (≥1, confirm), Nạp; Nhập/Xuất only where import/export exists (users) | no |
| A-04 | Column filters: text = case/accent-insensitive contains (unaccent ILIKE), select = exact, date = from/to; debounce 300 ms; page sizes 20/50/100, default 20 | no |
| A-05 | URL param names: `q`, `page`, `page_size`, `sort` (`field` or `-field`), and one param per column filter named after the API field | yes |
| A-06 | Bare-list endpoints become `Page`; small reference lists used by pickers (topics tree, taxonomy, tags for pickers) keep an unpaged variant via `page_size=all` capped at 1000 | no |
| A-07 | Students use the same shell; header org switcher shows the current org only until F7 | no |
| A-08 | Detail panel under the table (back-office "Chi tiết") for exams → questions and classes → students; other lists open a page or dialog | no |
| A-09 | Existing web tests are rewritten against the new markup; coverage kept at least at today's 84 cases | no |

ADRs: ADR-01 — shadcn components verbatim; ADR-02 — URL is the table state; ADR-03 — One paging helper on the API; ADR-04 — TanStack Table in manual mode; ADR-05 — shadcn NativeSelect in dense forms, Radix Select in tables and filters; ADR-06 — TanStack Table pinned to v8

### Assumptions — 2026092206-school-structure-multi-org

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | A school level (Cấp học) is an org-owned entity: code, name, grade range, sort; new orgs get THCS 6–9 and THPT 10–12; Tiểu học is not seeded | yes |
| A-02 | A grade (Khối) belongs to exactly one level; its grade number must lie in the level's range and is unique per org | yes |
| A-03 | A class belongs to one grade (`grade_id`); the old integer `classes.grade` stays as a cache so bank/exam filters keep working | no |
| A-04 | Deleting a level with grades, or a grade with classes, is refused (409 with the count); classes are deleted from the class list as today | no |
| A-05 | `users.organization_id` is the home org (where the username lives and the user logs in); `organization_members` holds (user, org, role, is_active) and is the source of permissions per org | yes |
| A-06 | Roles are per org; `users.role` mirrors the home membership so existing code keeps a meaning | no |
| A-07 | After login the last used org opens (`users.last_org_id`) if its membership is still active and the org can log in; otherwise the home org | no |
| A-08 | Switching org re-issues the access token; the refresh token follows `last_org_id` | no |
| A-09 | Super admin sees every org in the selector and works inside it with org_admin rights; audit records the super admin as actor | no |
| A-10 | An org admin (or super admin) of the target org adds an existing account by home org code + username and a role; removing a membership never deletes the account; the home membership cannot be removed | yes |
| A-11 | A suspended target org disappears from the selector; if it was active, the next request falls back to the home org | no |
| A-12 | The org detail "Thành viên" tab from the chat plan is replaced by "Vào tổ chức" (switch) + the normal Users page | no |

ADRs: ADR-01 — Levels and grades are org-owned rows; ADR-02 — Home org + memberships; ADR-03 — The token carries the active org; every request re-checks membership; ADR-04 — Super admin works inside orgs as org_admin

## 11. F8 `school-years` (2026-09-22)

Asked in chat: "Vì còn theo dõi học sinh xuyên suốt từ 10 → 12 … chia theo năm học", answers: HK1 & HK2; documents by Kỳ 1/Kỳ 2, giữa kỳ 1, giữa kỳ 2…; many classes, many orgs; Org ↔ Người dùng assignable from both screens; closed years editable with history.

**What changed**
- **Năm học** per org with HK1/HK2 dates, one "Đang học" year; header year selector (per org, remembered in the browser) scopes Lớp học, Cơ cấu trường, Báo cáo. Closed years stay editable; every change (and close/reopen) is in **Lịch sử**.
- **Answers remember** the year, the term and every class the student was in → class reports stay correct after students move; reports filter by year and HK.
- **Hồ sơ học sinh** (`/org/students/{id}`): one card per year — classes with status (lên lớp / ở lại / chuyển đi / tốt nghiệp), results per term and per top-level topic.
- **Chuyển năm học** wizard: 10A1 → 11A1, top grade → tốt nghiệp, exceptions per student, optional "make the new year active"; safe to run again.
- **Đợt kiểm tra**: one picker "Giữa kỳ 1 / Cuối kỳ 1 / Giữa kỳ 2 / Cuối kỳ 2 / Khảo sát · HK1 …" on upload, bank filters and labels (stored in the existing semester + kind fields).
- **Org ↔ user** for the super admin: Tổ chức → members panel; new **Tài khoản** page → organisations panel; both use the same service as the org admin's "Thêm tài khoản có sẵn".

**Dev data changed by the demo**: 2027-2028 (Chuẩn bị) created by the rollover with 11A1, 11A2, 10A1; 2026-2027 memberships marked "Lên lớp" except Đặng Thanh Quân "Ở lại lớp". 2026-2027 is still the active year.

**Known limits**: answer facts from before the migration got their year/term/classes from the answer date and today's memberships (best effort); a class belongs to exactly one year; the year choice is per browser, not per account.


### Assumptions — 2026092207-school-years

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | A school year belongs to an org: code "YYYY-YYYY", start/end dates, status planning / active / closed; exactly one active year per org | yes |
| A-02 | Terms are fixed: HK1 and HK2 per year with their own dates (defaults 05/09–15/01 and 16/01–31/05) | no |
| A-03 | A class belongs to one school year; a student may be in several classes of the same year and in several orgs | yes |
| A-04 | Closed years stay editable by org admins; every change to a closed year (and close/reopen itself) is written to the audit history, which is visible on the year, class and student | yes |
| A-05 | Enrollment status per class member: đang học / lên lớp / ở lại / chuyển đi / tốt nghiệp, with joined/left dates | no |
| A-06 | Each answer fact snapshots school_year_id, term (hk1/hk2 by date) and the ids of the student's classes in that year; class reports use the snapshot, not current membership | yes |
| A-07 | Rollover: target class name = source name with its leading grade number +1 (10A1 → 11A1); grade 12 (the org's highest grade) → tốt nghiệp; per student the admin can pick lên lớp / ở lại (same-name class in the new year) / chuyển đi / tốt nghiệp; the source year can be closed at the end | yes |
| A-08 | The header year selector is per browser and per org (localStorage), defaulting to the active year; year-scoped screens: Lớp học, Cơ cấu trường, Báo cáo, Giao bài lists | no |
| A-09 | Question bank, exams and accounts are not year-scoped | no |
| A-10 | "Đợt kiểm tra" = semester (hk1/hk2) × kind: Giữa kỳ 1, Cuối kỳ 1, Giữa kỳ 2, Cuối kỳ 2, plus Khảo sát / Thi thử / Ôn tập / Khác with a term; stored in the existing semester_code + exam_kind columns | no |
| A-11 | Org ↔ user assignment from both screens is a super-admin feature: org list → members panel; new "Tài khoản" (all accounts) list → organisations panel; org admins keep "Thêm tài khoản có sẵn" in their org | yes |

ADRs: ADR-01 — Classes belong to a school-year row; ADR-02 — Answer facts snapshot year, term and classes; ADR-03 — Idempotent rollover by (year, class name); ADR-04 — One membership service for both admin screens; ADR-05 — History is the audit log

Tests at close: API 246, web 120; tsc/eslint/build clean. Evidence: `.ai/features/2026092207-school-years/07-demo-evidence.md`.

## 12. Follow-ups after F8 (2026-09-22, chat feedback on screenshots)

- **Tables fill the screen**: only the table body scrolls; header + filter row + totals are sticky and the pagination stays at the bottom. List screens use `ListLayout`.
- **Table ↔ Chi tiết split is draggable** (shadcn `resizable`), remembered per screen: Lớp học, Đề thi, Tổ chức, Tài khoản; Cơ cấu trường has a draggable tree | table split on desktop and stacks on phones.
- **Pagination is responsive to its container** (not the viewport): labels, first/last buttons and the long summary drop out step by step (`‹ [1] / 2 ›  20  1–20 / 32` on a phone). The header's org/year selectors are compact on phones.
- **Topic filter is a tree**: checkbox tree with expand/collapse and accent-free search; choosing a parent includes all its children, choosing every child selects the parent; several branches can be combined. URL: `topic_ids=a,b` (each id includes its subtree on the server); old `topic_id` links still work.
- Known test-environment note: jsdom has no layout, so tests set values with `fireEvent.change` for inputs inside resizable panels.
- Tests: API 246, web 123; tsc/eslint/build clean.


## 13. F9 `2026092208-official-exam-ingestion` — đọc đúng đề chính thức (2026-09-22)

Trigger: "@Examin/ Đây là tài liệu chính thức, có thể làm mẫu được. Tham khảo tài liệu, thiết kế lại DB, UI,UX…"

- **MathType → LaTeX** (`ingestion/mtef.py`, own MTEF v5 reader): 7 889/7 889 formulas of the 18 files read, KaTeX renders
  100 %, 90 random ones compared by eye with the originals. Unreadable objects keep their picture with a warning.
- **WMF/EMF → PNG** via LibreOffice headless (API/worker image now ~1.6 GB, +LibreOffice Draw): 31 figures, 0 lost.
- **THPT 2025 layout**: per-part answer tables in the solutions, "a đúng| b sai", Đ/S grids, header-less solution pass,
  Word auto-numbered parts, Cyrillic "А", underlined/highlighted labels, copied question removed from the solution,
  "Phương pháp / Cách giải" kept as headings.
- **Result on the 18 files (live, 24 s)**: 396/396 questions, 393 with an answer (the 3 others have none in the file),
  386/386 solutions. 17 questions flagged "đáp án không khớp bảng đáp án" where the file's key disagrees with its own
  worked solution (ĐHKHTN key is another mã đề; Sở Bắc Ninh Phần III key shifted a column) — the solution wins.
- **Header → metadata**: issuer, school year, subject, lớp, kỳ, lần, thời gian filled when the uploader left them on
  "Tự nhận từ đề"; editable on the document ("Sửa thông tin") and applied to its questions + nguồn tag.
- **Upload many files at once**; **"Tạo đề từ tài liệu"** makes a draft exam in PHẦN/Câu order (0,25 / 1 / 0,5).
- Golden: `tests/golden/official_expected.json` (derived data only; files stay outside the repo, `EXAMIN_DIR=…`).

### Assumptions — 2026092208-official-exam-ingestion

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | The 18 files in `Examin/` are representative of the official files centers upload (MathType OLE, three-part THPT 2025 layout, solution section repeating questions) | yes |
| A-02 | MathType is converted by our own MTEF v5 reader (no maintained Python package exists); template/embellishment numbering follows the MathType SDK as used by zhexiao/mtef-go (Apache-2.0, credited) | yes |
| A-03 | WMF/EMF pictures are rendered with LibreOffice headless (→ PDF → pypdfium2 PNG, trimmed); the API/worker image grows by ~300 MB; without soffice the old warning path applies | no |
| A-04 | "Phương pháp" and "Cách giải" stay inside the solution markdown as bold sub-headings, not separate columns | no |
| A-05 | Header metadata (issuer, school year, subject, exam kind, attempt, duration) is a suggestion shown in the upload/document form; the user's values win | no |
| A-06 | "Tạo đề từ tài liệu" makes a draft exam with the document's parsed questions in original part/number order, points 0,25 (Phần I), 1 with THPT partial ladder (Phần II), 0,5 (Phần III) | no |
| A-07 | Multi-file upload creates one document per file with the same processing settings; duplicates (same hash) are reported per file and skipped | no |
| A-08 | Expected answers for the golden set are taken from each file's own answer tables and spot-checked by hand; the files stay outside the repo (only derived expectations are committed) | no |

ADRs: ADR-01 Own MTEF v5 reader; ADR-02 Tokens before Pandoc; ADR-03 LibreOffice renders WMF/EMF; ADR-04 Answers from the file's own tables; ADR-05 Header metadata as suggestions in meta.

## 14. F10 `2026092209-subject-scoped-bank` — bộ lọc theo môn (2026-09-22)

Answer to "Bộ lọc nên phân theo từng môn không?": yes — the subject is the bank's working context.

- **Tabs Môn** at the top (with counts; last used per browser + org; "Chưa phân môn" when needed). Switching subject
  drops topic and tag filters, keeps the rest.
- **"Bộ lọc" sheet** (right side, full screen on phones): Chuyên đề tree with subtree counts, Loại câu, Mức độ, Lớp,
  Đợt, Năm học, Nguồn đề, Tags by group, Trạng thái — every option with a count (each facet ignores its own filter).
  "Áp dụng" writes the URL; **chips** under the search remove one filter; "Xóa tất cả".
- **Tags by subject** (migration 0016, nullable `tags.subject_id`, backfill); nguồn đề always shared. Tags page has a
  Môn column + subject in the form; exam matrix and question editor only offer the subject's topics/tags.
- Several tags: OR inside a group, AND across groups (e.g. nguồn đề AND phương pháp).

### Assumptions — 2026092209-subject-scoped-bank

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | Subject is the working context of the bank: tabs at the top, always one chosen; questions without a subject have their own "Chưa phân môn" tab (shown only when there are any) | yes |
| A-02 | Tags get an optional subject; no subject = shared by all subjects; source tags (nguồn đề) are always shared; backfill gives a tag the subject of its questions when they all share one | yes |
| A-03 | The chosen subject is remembered per browser and org (localStorage), like the header year selector — not in the user row as the plan first said | no |
| A-04 | Filters live in a right-side "Bộ lọc" sheet with sections and counts; counts are computed with every other filter applied (a facet ignores its own dimension); topic counts include the subtree | no |
| A-05 | The sheet edits a draft and applies on "Áp dụng"; chips remove one filter at once; the search box stays on the page | no |
| A-06 | "Năm học" filters by the source document's school year (manual questions have none) | no |
| A-07 | The exam matrix (BlueprintEditor) lists topics and tags of the exam's subject only | no |

ADRs: ADR-01 Subject as the bank's context; ADR-02 Facets exclude their own dimension; ADR-03 Optional subject on tags.

## 15. F11 `2026092210-ui-polish-dialogs-tables` (2026-09-22, back-office screenshots)

- Dialogs: ⤢ Phóng to / Thu nhỏ (also double-click the title), drag any edge or corner. **Please check the drag by
  eye** — the in-app browser pane was hidden during the demo, so only the jsdom test measured it.
- Tables: column borders, zebra rows, sticky header + filter row.
- "←" on detail pages returns to the list's page, sort and filters (bank, documents, exams, classes, review).
- Topic picker is a tree everywhere; ⌘/Ctrl + Enter saves (also while typing Vietnamese); hint shows ⌘ on Mac.
- Compact paddings for small screens.

### Assumptions — 2026092210-ui-polish-dialogs-tables

| ID | Assumption | Blocking |
| --- | --- | --- |
| A-01 | Every FormDialog gets ⤢ maximise (also double-click on the title) and edge/corner resizing; sizes reset when the dialog closes | no |
| A-02 | Back links and "Hủy/Lưu" returns go to the last URL of that list in this tab (sessionStorage), falling back to the plain list | no |
| A-03 | The save shortcut listens to the physical Enter key (`code`) with ⌘ or Ctrl, so Vietnamese IME composition does not swallow it; the hint shows ⌘ on Apple devices | no |
| A-04 | Question editor topics are limited to the question's subject when it has one (as in the bank, F10) | no |

ADRs: ADR-01 Resizing in the app wrapper, not the shadcn file; ADR-02 List memory in sessionStorage.

Tests at close of F9–F11: API 298 (incl. the 18 official files), web 134; tsc/eslint/next build clean.

## 16. Follow-ups after F11 (2026-09-22, chat feedback on screenshots)

- **Broken formulas `_{…}` in the bank**: some Word files put a MathType object in a run formatted as sub/superscript
  (for alignment); it became `$_{$…$}$`. The sub/superscript wrapper is now dropped around formulas and pictures.
  All 7 885 inline formulas of the 18 files render in KaTeX. Every .docx was re-parsed on the dev stack.
- **Re-parse bug found**: re-parsing deleted unapproved questions that an exam used (FK error, document "failed").
  Questions used in an exam are now kept, like approved ones (test added).
- **"Chưa phân môn" emptied**: re-parsing filled subjects from the headers; the files without a MÔN line (Quế Võ 1,
  internal samples) were set to Toán via "Sửa thông tin". All 1 055 dev questions are Toán.
- **Markdown editor with preview**: stem, options, solution and model answer have a toolbar (đậm, nghiêng, $…$, $$…$$,
  phân số, căn, mũ, chỉ số, vectơ, góc, ≤ ≥ ≠ ∈ ∞ ⇔, hệ, chèn ảnh) and a live KaTeX preview under the field
  (errors show in red); options show it while focused or when they contain markup.
- **Đề thi & giao bài**: the list fetches only exams; choosing a row loads its questions through the shared DataTable
  (no toolbar, server paging/filters `/exams/{id}/questions`, sticky header), rendered with formulas, bold and
  pictures. Clicking the exam title opens a (resizable) dialog with the whole exam by PHẦN, fetched on open.
- Sticky headers: DataTable headers were already sticky (checked live); the non-sticky one was the old plain table in
  the exam detail, now replaced.
- Tests: API 300 (incl. 18 official files), web 137; tsc/eslint/next build clean.

## 17. F12 `2026092211-ui-standards` (2026-09-22)

- **Duplicate uploads (critical)** — cause: my golden runner uploaded modified copies of the 18 files; your real
  upload had other hashes, so nothing matched, and there was no choice. Now the upload form checks every file first:
  same content → "Bỏ qua (dùng bản đã có)" / "Tách lại bản đã có"; same name → "Ghi đè bản cũ" / "Giữ cả hai" /
  "Bỏ qua", with "apply to all". The same content is never stored twice. The runner now re-parses in place.
  Done on Loc Tran's go: the 18 old copies, their questions and 539 images deleted (backup `backups/examind-before-dedupe-*.dump`),
  the Ninh Bình exam and its assignment re-created from the real upload. Bug found meanwhile: questions marked "duplicate"
  of a deleted original stayed hidden — they now return to review (test added).
- **Filters like the reference**: symbol button per column — text `*` Chứa, `=` Bằng, `+` Bắt đầu bằng, `-` Kết thúc bằng,
  `!` Không chứa; numbers/dates `=` `<` `≤` `>` `≥`; dates also "↔ Trong khoảng" (default). URL `<col>_op`, server whitelist.
  Deviations from the back-office: kept in the URL (not a POST body); text `=` ignores accents/case.
- **Time**: UTC in DB/API as before; display and day filters fixed to Asia/Ho_Chi_Minh (`BUSINESS_TZ`), date-time inputs
  send +07:00; school year/term of answers use the Vietnamese day. The back-office's two known zone bugs are avoided.
- **Exam order**: "Sắp xếp thứ tự" draft (swap with a chosen câu, drag, ↑/↓, inside a PHẦN) saved once.
- **shadcn everywhere**; exam preview dialog fills when maximised.
- **Last question polluted (found by Loc Tran)**: every official file's last question (and often its solution) carried
  "HẾT" and the exam header repeated before the solutions ("SỞ GIÁO DỤC…", "KÌ THI…", "Mã đề thi…", "1.B | 2.C …").
  The splitter now treats "HẾT" and exam-header lines as a boundary that closes the question, and reads "n.X | n.X …"
  rows as answer keys anywhere (test added; golden unchanged). All 18 files re-parsed; the Ninh Bình exam + assignment
  re-created (no attempts existed); every unused image deleted (524 → 263 images left, all referenced; 0 orphans).

## 18. Follow-up: bỏ hết control native (2026-09-22, ảnh chụp ma trận đề)
- **Nguyên nhân sót:** lần rà trước chỉ grep thẻ `<select>`. Nó bỏ sót component `NativeSelect` (bọc `<select>` thật, 25 chỗ trong 12 file) và các ô `type="date"` / `datetime-local` (13 chỗ).
- **Select:** cả 25 chỗ NativeSelect đã chuyển sang `OptionSelect`, tức Select popover của shadcn, nay có thêm `disabled` cho từng option. Các chỗ đã đổi:
  - ma trận đề (BlueprintEditor);
  - form câu hỏi, sửa câu hỏi, cây chuyên đề, trang chuyên đề;
  - báo cáo, model AI, cấu hình tách đề;
  - metadata tài liệu, giao bài, kế hoạch lên lớp.
- **Ngày/giờ:** thêm `components/ui/calendar` (lấy qua shadcn CLI) và `components/app/DatePicker.tsx`.
  - `DatePicker` giữ giá trị `YYYY-MM-DD`, hiển thị dd/MM/yyyy, lịch tiếng Việt có dropdown tháng/năm và nút xoá.
  - `DateTimePicker` giữ nguyên hợp đồng `datetime-local` (`YYYY-MM-DDTHH:mm`, giờ nghiệp vụ +07:00): chọn ngày trên lịch, gõ giờ HH:mm. Chọn ngày mà chưa có giờ thì mặc định 07:00.
  - Đã áp dụng ở: YearForm (6 ô), Giao bài (mở/đóng), Giao bài thích ứng (mở/đóng), bộ lọc cột kiểu ngày của DataTable (khoảng và một ngày).
- **Chặn tái phát:** ESLint báo lỗi khi import `ui/native-select`, dùng `<select>`, hoặc dùng `type="date|datetime-local|time|month|week"` ngoài `components/ui`.
- **Kiểm tra:** tsc/eslint sạch; vitest 144/144, trong đó có test mới `date-picker.test.tsx`.
  - Kiểm tra trên trình duyệt, cả trang lẫn dialog Giao bài không còn `<select>` hay ô ngày native. Riêng dialog có một `<select aria-hidden>`: đó là thẻ ẩn Radix tự thêm để gửi form, không phải control hiển thị.
