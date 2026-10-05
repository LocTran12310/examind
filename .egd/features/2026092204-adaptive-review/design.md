---
feature: adaptive-review
adr_count: 3
---

# Logical design — Adaptive review

## Approach
A `mastery` service updates `student_topic_mastery` whenever answer facts are written for a
leaf topic (hook in `attempts._fact`), and can rebuild it from all facts (backfill). An
`adaptive` service composes a review exam: rank the student's leaf topics by mastery, draw
from weak/medium topic subtrees with difficulty targeting, add wrong-answer re-asks, exclude
recent correct and non-usable questions, then persist it as an `Exam(source=adaptive)` and
start a practice attempt (student) or create per-student assignments (teacher). A `key_audit`
service runs in the worker to flag MCQs whose top-quartile answers contradict the key.

## Alternatives considered
| Option | Why not |
| --- | --- |
| BKT/IRT now | Needs more data than a new center has; EMA is transparent and cheap — upgrade path kept (mastery is one table) |
| Recompute mastery on every read | Grows with history; incremental update is O(answers in one attempt) |
| Auto-fix suspected keys | Too risky; a teacher confirms in the existing review queue |

## Domain model
| Entity | Fields | Notes |
| --- | --- | --- |
| `StudentTopicMastery` | organization_id, student_id, topic_id, mastery 0–1, answers, last_at | PK (student, topic) |
| `Question` (+) | status `flagged`; `issues` gets "Nghi sai đáp án"; `flag_evidence` jsonb | |
| `Exam` | `source = adaptive`, `settings.adaptive` = {student_id, plan} | hidden from the exams list |

## Contracts
| Method & path | Role | Notes |
| --- | --- | --- |
| `GET /me/mastery` · `GET /students/{id}/mastery` | student (own) · staff | rows with rolled-up parents |
| `POST /me/practice` `{count?}` | student | creates adaptive exam + attempt → `{attempt_id, plan}` |
| `POST /classes/{id}/adaptive-assignments` `{count, open_at, close_at, duration_minutes}` | staff | `{created: n}` |
| `GET /classes/{id}/overview` | staff | students with weakest topics and review status |
| `POST /review/key-audit` | staff | run detection now → `{flagged}` |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Mastery | `student_topic_mastery`, updated on grading | persistent |
| Review plan (why each question was chosen) | `exams.settings.adaptive.plan` | persistent, shown to the student |

## Failure modes
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Bank too small for a review exam | 200 with fewer questions + note | — | note on result |
| No usable questions at all | `empty_bank` | 409 | message |
| Teacher targets another org's class | `not_found` | 404 | — |

## Observability
Detection logs flagged question ids with evidence; review plan stored with each adaptive exam.

## ADRs

### ADR-01 — Difficulty-weighted EMA mastery on leaf topics
**Context:** Need a per-topic signal from day one with little data.
**Decision:** EMA α 0.3 over correctness ratio with difficulty weights; parents aggregated at read time.
**Consequences:** Explainable, O(1) updates; swap for BKT later without changing callers.
**Status:** accepted

### ADR-02 — Adaptive exams are ordinary exams
**Context:** Reuse taking, grading, results and reports.
**Decision:** Persist generated review sets as `Exam(source=adaptive)`; practice = attempt without assignment; class mode = one assignment per student.
**Consequences:** No new taking flow; the exams list hides adaptive exams.
**Status:** accepted

### ADR-03 — Top-quartile key audit
**Context:** Wrong keys hurt good students most.
**Decision:** Compare the key with what the top-quartile students chose; flag, never auto-edit; flagged questions leave the usable pool until approved.
**Consequences:** Needs ≥ 10 answers; hard-but-correct questions are protected by the top-quartile rule.
**Status:** accepted
