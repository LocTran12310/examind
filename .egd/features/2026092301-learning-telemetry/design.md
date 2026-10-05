---
feature: learning-telemetry
adr_count: 4
---

# Logical design

## Approach
Three slices, each demoable on its own: the answer carries its evidence (timing, attempt number, and no fact for
an unanswered question); statistics per question read from those facts; mastery rules repaired plus a weekly
snapshot so a trend exists before the screens that draw it.

- **Assessment** owns the timing fields and decides what becomes a fact. The runner reports `seconds_spent`
  with each save; the server clamps it to `[0, attempt window]` and accumulates per question (so a student who
  returns to a question adds time). `attempt_answers` gains `first_seen_at`, `seconds_spent`, `answered_at`,
  `save_count`; `answer_facts` gains `seconds_spent`, `first_attempt` (no earlier fact for that
  student+question) and `answered_at`.
- **Bank** owns item statistics: a read model over `answer_facts` joined to `attempts` for the score ranking,
  exposed on the question detail and as searchable columns. `key_audit` moves onto the same read model instead
  of computing its own ratios.
- **Analytics** owns the mastery rules: one `weak_topics()` in the domain used by the planner, the API and the
  UI; decay applied in `step()`/`rollup()`; `POST /analytics/mastery/rebuild` for an organisation; a weekly
  snapshot table written by the worker and backfillable from facts.

## Alternatives considered
| Option | Why not |
| --- | --- |
| Server-side timing only (grade time − start time) | Cannot attribute time to a question; useless for item difficulty |
| A general event log (xAPI-style) | Three columns on the tables we already have answer the questions we actually ask |
| Nightly recomputation of every statistic into its own table | Read models over `answer_facts` are fast enough at this volume and cannot go stale |
| Decay as a background job | Touching every row nightly to change a number nobody read; compute it on read instead |

## Domain model
`attempt_answers` += `first_seen_at timestamptz`, `answered_at timestamptz`, `seconds_spent int`, `save_count int default 0`.
`answer_facts` += `seconds_spent int`, `answered_at timestamptz`, `first_attempt bool`.
New `student_topic_week(student_id, topic_id, organization_id, week_start date, mastery float, answers int)`, PK
`(student_id, topic_id, week_start)`.

## Contracts
| Method & path | Notes |
| --- | --- |
| `POST /attempts/{id}/answers` | body gains `seconds_spent` (optional int) and `first_seen_at` |
| `GET /questions/{id}/stats` | `{observations, correct_ratio, first_attempt_ratio, discrimination, median_seconds, options: [{label, chosen, ratio}], enough_data}` |
| `POST /questions/search` | filters/sorts gain `stats_observations`, `stats_correct_ratio` |
| `POST /analytics/mastery/rebuild` | org admin; `{students, topics, facts}` replayed |
| `GET /students/{id}/mastery/weekly`, `GET /me/mastery/weekly` | `{weeks: [{week_start, topics: [{topic_id, mastery, answers}]}]}` |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Seconds per question | the runner while answering, then `attempt_answers` | the attempt |
| Item statistics | derived from `answer_facts` on read | — |
| Weekly mastery | `student_topic_week` | kept |

## Failure modes
| Condition | Code | HTTP |
| --- | --- | --- |
| `seconds_spent` negative or beyond the window | clamped, no error | 200 |
| Rebuild by a non-admin | `forbidden` | 403 |
| Stats for a question of another organisation | `not_found` | 404 |

## Observability
The rebuild logs students, topics and facts replayed; the weekly job logs rows written; the ingest-style step
log is not extended.

## ADRs

### ADR-01 — Timing is reported by the client and clamped by the server
**Context:** Only the browser knows when a question was on screen; only the server can be trusted with totals.
**Decision:** The runner sends `seconds_spent` per save; the server accumulates and clamps to the attempt window,
and stores `first_seen_at` / `answered_at`. Timing is treated as evidence for difficulty, never for discipline.
**Consequences:** Offline or tampered clients can under-report; statistics use the median, which tolerates it.
**Status:** accepted

### ADR-02 — An unanswered question produces no fact
**Context:** Abandoned practice currently lowers mastery, punishing the student for opening it.
**Decision:** Grading still scores unanswered questions 0 for the exam result, but writes no `answer_fact`, so
mastery, reports and item statistics ignore them.
**Consequences:** Report denominators become "answers", not "questions assigned"; a separate "bỏ trống" count is
available from the attempt when someone asks for it.
**Status:** accepted

### ADR-03 — Item statistics are read models with a minimum of observations
**Context:** A p-value from three answers is noise, and a hand-typed difficulty label is not calibration.
**Decision:** Compute share correct, first-attempt share, discrimination (top third vs bottom third of attempt
score), median seconds and option counts from `answer_facts`; below 10 observations report `enough_data: false`
and show nothing else. The stored `difficulty` label stays as the teacher's intent; calibration comes later.
**Consequences:** No new table to keep in sync; the bank can sort by observed difficulty.
**Status:** accepted

### ADR-04 — One weak-topic rule, decay on read, recompute on demand
**Context:** Three definitions, no decay, no supported recompute.
**Decision:** `weak_topics(rows)` in the analytics domain is the only definition (mastery < 0.6, answers ≥ 5);
decay toward 0.5 with a 60-day half-life is applied where mastery is read or updated, from `last_at`;
`POST /analytics/mastery/rebuild` replays facts for one organisation.
**Consequences:** Existing numbers move the first time they are read; the rebuild makes that reproducible.
**Status:** accepted
