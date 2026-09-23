# Demo evidence — learning-telemetry

## UOW-01 — Answers carry timing, attempt number and no fact when unanswered (2026-09-23, live stack)

Migration `0017` applied by the api container on start (`alembic_version` = 0017); `alembic check` clean
(`test_schema_drift.py`). `attempt_answers` += `first_seen_at`, `answered_at`, `seconds_spent` (0), `save_count` (0);
`answer_facts` += `seconds_spent`, `answered_at`, `first_attempt` — existing rows keep nulls / zero, nothing backfilled.

### AC-01 — timing accumulates, is clamped, and reaches the fact
Two attempts of a 22-question exam as `buivanchau`, taken over the API:
- attempt `d36548f4`, started 04:04:46. Saves on one question: 30 → **30**, +22 → **52**, −40 → **52** (nonsense costs
  nothing), +999999 → **60** = the whole attempt window so far (`started_at` → now). `save_count` 4,
  `first_seen_at` 04:04:46.6 (reported by the client), `answered_at` 04:05:46.8.
- its fact: `seconds_spent` 60, `answered_at` 04:05:46.8, `first_attempt` **false** — the same question had been
  answered in the earlier attempt `8c7e8727`; the second question of the run got `first_attempt` **true**, 9 seconds.

### AC-01 — the runner measures it (browser, http://localhost:8088)
Attempt `56745186` taken in the exam runner: ~35 s on câu 1, answer B, 18 s on câu 2, back to câu 1 for ~20 s, answer C,
"Nộp bài". The two saves the runner sent added up to `seconds_spent` **57** over 75 s of wall clock — the 18 s spent on
câu 2 are not counted — with `first_seen_at` 04:06:49.3, one second after the attempt started. Countdown and the
"Đã lưu / Chưa lưu" badge behave as before.

### AC-02 — an unanswered question produces no fact
Each of the three attempts wrote 22 `attempt_answers` rows and scored the blanks 0 (`score` 0 / `max_score` 10), but
only the answered questions became facts: 2, 2 and 1. Over the whole student: **5 facts for 66 questions**, 4 of them
first attempts, 126 seconds in total; `student_topic_mastery` holds 4 rows / 5 answers, so nothing moved for a question
nobody answered. The same rule is exercised for the expiry sweep and for essay re-grading in the suites below.

### Checks
- `make lint-api` (ruff + 4 import contracts), `./scripts/verify.sh apps/api/tests`: **415 passed, 1 skipped**
  (87 of them handler tests on fake ports).
- `cd apps/web && pnpm typecheck`, `pnpm lint`, `pnpm test`: **172 passed** in 49 files.
- New tests: `test_attempts_api.py::test_timing_accumulates_over_the_saves_and_reaches_the_fact` and
  `::test_an_abandoned_attempt_leaves_no_facts_and_no_mastery`;
  `tests/unit/test_assessment_handlers.py` — timing clamp, unanswered question, swept attempt, first attempt;
  `exam-runner.test.tsx` — the saved body carries the seconds and they add up when a question is revisited.
