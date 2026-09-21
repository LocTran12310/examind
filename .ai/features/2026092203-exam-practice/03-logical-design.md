---
feature: exam-practice
adr_count: 6
---

# Logical design — Exams, practice and statistics

## Approach
Exams are ordered lists of bank questions with per-question points (`exam_questions`). A
builder service fills them from blueprint rows using `bank.search` filters and a seeded random
draw. Assignments bind an exam to classes/students with a time window and policies. Taking an
exam creates an `attempt` with its own shuffled question/option order and a server-computed
deadline; answers are upserted per question; submit (or expiry, detected lazily on every
access and by a worker sweep) finalises and grades via a pure `scoring` module, writing one
`answer_facts` row per answer (denormalised topic path, tags, type, difficulty, points).
Reports are SQL aggregates over `answer_facts`, rolling topic levels up with `ltree`.

## Alternatives rejected
| Option | Why not |
| --- | --- |
| Materialised view refreshed after each submit | Refresh cost grows with the whole table; per-answer insert is incremental and cheap |
| Client-side timer as source of truth | Trivially bypassed; the server deadline decides |
| Copy questions into exams | Duplicates content and edits; answers keep a grading snapshot instead |
| WebSockets for autosave | Plain PUT per change (debounced) is simpler and works on flaky mobile networks |

## Domain model
| Entity | Fields | Notes |
| --- | --- | --- |
| `Exam` | id, org, title, subject_id, grade, description, settings jsonb {points_by_type, scale_to}, blueprint jsonb [rows], source manual/blueprint/adaptive, created_by, created_at, updated_at | |
| `ExamQuestion` | exam_id, question_id, position, section, points, row | PK (exam, question) |
| `Assignment` | id, org, exam_id, title, open_at, close_at, duration_minutes, max_attempts, shuffle_questions, shuffle_options, results_policy after_submit/after_close/never, created_by | |
| `AssignmentTarget` | assignment_id, class_id?, user_id? | |
| `Attempt` | id, org, assignment_id?, exam_id, student_id, started_at, deadline_at, submitted_at, status in_progress/submitted, score, max_score, needs_grading, question_order jsonb, option_orders jsonb, tab_switches | |
| `AttemptAnswer` | attempt_id, question_id, response jsonb, is_correct, points, max_points, key_snapshot jsonb, comment, graded_by, updated_at | PK (attempt, question) |
| `AnswerFact` | id, org, attempt_id, assignment_id?, exam_id, student_id, question_id, topic_path ltree?, tag_ids uuid[], qtype, difficulty, points, max_points, correct_ratio, created_at | GiST(topic_path) |

## Contracts
| Method & path | Role | Notes |
| --- | --- | --- |
| `GET/POST /exams`, `GET/PATCH/DELETE /exams/{id}` | staff | exam with questions (ParsedQuestionOut + points, section) |
| `POST /exams/{id}/blueprint` `{rows, seed?}` | staff | `{added, shortfalls:[{row, missing}]}` |
| `POST /exams/{id}/questions` `{question_ids}` · `DELETE /exams/{id}/questions/{qid}` · `PUT /exams/{id}/order` · `POST /exams/{id}/questions/{qid}/swap` · `PATCH /exams/{id}/questions/{qid}` `{points}` | staff | |
| `GET/POST /assignments`, `GET/PATCH/DELETE /assignments/{id}` | staff | targets = class_ids + user_ids |
| `GET /assignments/{id}/report` | staff | students, distribution, per-question stats |
| `GET /me/assignments` | student | open / upcoming / done |
| `POST /assignments/{id}/start` | student | returns attempt (existing in-progress attempt is resumed) |
| `GET /attempts/{id}` | owner student / staff | student view hides keys until result policy allows |
| `PUT /attempts/{id}/answers/{qid}` `{response}` | owner | 409 `attempt_closed` after deadline |
| `POST /attempts/{id}/submit`, `POST /attempts/{id}/tab-switch` | owner | |
| `GET /attempts/{id}/result` | owner / staff | per policy |
| `PATCH /attempts/{id}/answers/{qid}/grade` `{points, comment}` | staff | essays (and overrides) |
| `GET /stats/topics` `?class_id&student_id&assignment_id&from&to&subject_id` | staff (students: own) | tree rows {topic, correct, answered, ratio} |
| `GET /stats/groups?by=tag|type|difficulty&…` | staff (students: own) | |
| `GET /stats/heatmap?class_id&level=1|2` | staff | |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Deadline, submission | server (`attempts`) | persistent |
| Current question, pending autosaves | exam page client state (debounced queue) | page |
| Aggregates | computed per request from `answer_facts` | request |

## Error taxonomy
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Assignment not open / closed / no attempts left | `not_open` / `closed` / `no_attempts_left` | 409 | message on home |
| Answer after deadline | `attempt_closed` | 409 | exam page switches to "Đã hết giờ" and shows result |
| Invalid response shape | `validation_error` | 422 | ignored with toast |
| Result hidden by policy | 200 with `hidden: true` | — | "Kết quả sẽ có sau …" |
| Delete question used in an exam | `question_in_use` | 409 | bank message |
| Blueprint row unfillable | 200 with shortfalls | — | warning per row |

## Cache & offline
Exam page keeps unsent answers in memory and retries every 3 s; a banner shows "Chưa lưu" until the server confirms.

## Observability
Attempt events (start, submit, auto-close, tab switch) logged with ids; answer_facts gives all reporting.

## ADRs

### ADR-01 — answer_facts written at grading time
**Context:** Reports slice by topic level, tag, type, difficulty, class, student, time.
**Decision:** One denormalised row per graded answer with the question's primary topic path and tags at grading time; aggregates are GROUP BY queries with ltree roll-up.
**Consequences:** Re-tagging a question later does not rewrite history (reports reflect what was known when answered); a backfill command can rebuild facts if needed.
**Status:** accepted

### ADR-02 — Server-authoritative deadlines with lazy + swept closing
**Context:** Students may close the tab when time is up.
**Decision:** `deadline_at` fixed at start; every attempt access finalises an expired attempt; the worker sweeps expired in-progress attempts every minute.
**Consequences:** Scores appear even if the student never comes back.
**Status:** accepted

### ADR-03 — Grading snapshot per answer
**Context:** Questions can be edited after being answered.
**Decision:** `attempt_answers.key_snapshot` stores the answer key used; points are computed once at submission (essays when graded).
**Consequences:** History is stable; re-grading after a key fix is an explicit action (future).
**Status:** accepted

### ADR-04 — Pure scoring module
**Context:** THPT 2025 partial credit and short-answer normalisation need exact, testable rules.
**Decision:** `app/services/scoring.py` with pure functions per type; configurable points and scale.
**Consequences:** Adaptive practice (feature 5) reuses the same grading.
**Status:** accepted

### ADR-05 — Grouped sidebar navigation
**Context:** Staff navigation outgrew a single top bar.
**Decision:** Sidebar with groups (Đề & câu hỏi, Lớp & học sinh, Báo cáo, Cài đặt); collapses to a drawer on phones; students keep a minimal top bar.
**Consequences:** Nav config becomes grouped data in `lib/nav.ts`.
**Status:** accepted

### ADR-06 — Shuffled options are relabelled per attempt
**Context:** Live demo: shuffled MCQ options showed their original labels (C, B, D, A).
**Decision:** The student view relabels options A–D in the attempt's order; answers are mapped back to the original label before storage; results map key and response back to display labels.
**Consequences:** Grading and answer_facts always use original labels; students always see A–D in order.
**Status:** accepted
