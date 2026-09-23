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

## UOW-02 — Item statistics per question, searchable (2026-09-23, live stack)

No migration: everything is read from `answer_facts` (joined to `attempts` for the score ranking) and from
`attempt_answers.response` for the option counts — one read model, `SqlItemStatsReader`, in `modules/bank`.

### The data I made
The live centre had 5 answer facts, so I created two exams of three multiple-choice questions and took **24 attempts**
of my own (`buivanchau` plus three students I created, `hsthongke1..3`; `max_attempts` 5). Nothing existing was
touched or deleted; the org now holds 77 facts. Four attempts of each ability (all right / only the first question /
none, with two lucky guesses), so the strongest and the weakest third of the attempts differ by design.

### AC-03 — the numbers on the question detail (http://localhost:8088/org/bank/<id>)
`GET /questions/398b4b80/stats` and the panel "Thống kê từ bài làm" agree:

| | |
| --- | --- |
| Tỉ lệ đúng | **67 %** (12 lượt) |
| Đúng ngay lần đầu | **75 %** (12 lượt) |
| Độ phân biệt | **+1.00** (12 lượt) |
| Thời gian trung vị | **25 giây** (12 lượt) |
| Phương án đã chọn | A ✓ đáp án 67 % (8 lượt) · B 17 % (2) · C 17 % (2) · D 0 % (0) |

Two more questions of the same exam read 33 % / +1.00 / 18 giây and 50 % / +0.50 / 15 giây; the seconds come from
the runner's own measure of UOW-01 (a save that reports more than the attempt window is still clamped — the first
batch of twelve attempts, answered in under a second, honestly reports a median of 0).

A question with two answers (`808d6e3a`) shows **"Chưa đủ dữ liệu — cần ít nhất 10 lượt trả lời (hiện có 2)."** and
no number at all; the endpoint answers `{"observations": 2, "enough_data": false, …}` with every metric null and no
options. Checked on desktop (dark) and at 375 px (light): under `sm` the bars drop out so the labels stay readable.
Another organisation's question is 404 `not_found`.

### AC-04 — the bank searched by what was observed
`POST /questions/search` gained `stats_observations` and `stats_correct_ratio` (number: `= < <= > >=`, `from`/`to`),
filterable and sortable, aggregated in one grouped sub-select joined only when a request names one of them:
- `stats_observations >= 10` → **6** questions (the six I answered), `>= 10` and `stats_correct_ratio <= 0.4` → **2**
- sorted by `stats_correct_ratio` ascending: the two hardest first, the easiest last; a question nobody answered
  counts as 0 observations and keeps its place in the list
- `{"operator": "+"}` on a number column → 422 `bad_filter`, an unknown `stats_*` field → 422 `bad_filter`,
  an unknown sort field → 422 `bad_sort`

### The key audit moved onto the same read model
`SqlAnswerStats` is gone: `mcq_answers` now lives on `SqlItemStatsReader` and shares the score-ratio expression with
the discrimination ranking, and `key_audit.MIN_ANSWERS` is the `MIN_OBSERVATIONS` of the new domain rule. The
flagging rule itself is unchanged; `POST /review/key-audit` on the live stack answers `{"flagged": []}` as before and
`tests/test_key_audit.py` is untouched and green.

### Checks
- `make lint-api` (ruff + 4 import contracts), `./scripts/verify.sh apps/api/tests`: **425 passed, 1 skipped**
  (415 before), 89 of them handler tests on fake ports.
- `cd apps/web && pnpm typecheck`, `pnpm lint`, `pnpm test`: **174 passed** in 49 files (172 before).
- New tests: `tests/test_item_stats.py` — the threshold at nine and ten answers, a question nobody answered,
  first-attempt share and a median that ignores missing seconds, discrimination +1 and −1 on a constructed set,
  option counts with the key marked, another organisation's question, the two search columns and their 422s;
  `tests/unit/test_bank_handlers.py` — the handler blanks every number below the minimum and 404s across orgs;
  `question-edit.test.tsx` — the panel's numbers with their counts and the option distribution, and "Chưa đủ dữ liệu".
