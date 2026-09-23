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

## UOW-03 — One weak-topic rule, decay, recompute and a weekly snapshot (2026-09-23, live stack)

Migration `0018` applied by the api container on start (`alembic_version` = 0018); `alembic check` clean
(`test_schema_drift.py`). New `student_topic_week(student_id, topic_id, week_start)` — empty on upgrade, filled by the
bootstrap backfill and kept by the worker. Nothing else in the schema moved.

### AC-05 — one rule, and "chưa đủ dữ liệu" instead of a guess
`weak_topics()` in `analytics/domain/services/mastery.py` is now the only definition (mastery < 0.6 **and** ≥ 5 answers);
`weakest()`, the planner's `< 0.8` and the web's `< 0.5` band are gone. `/me/mastery` carries `enough_data` and `weak`,
so the screen reads the flags instead of a threshold of its own.

`buivanchau` (org `trungtama`) over `GET /api/me/mastery`, 8 tracked topics:
- **Giá trị lớn nhất, nhỏ nhất** — 0.441, **5** answers → `enough_data: true`, `weak: true` → "Cần ôn".
- **Tích vô hướng của hai vectơ** 0.350 (1), **Logarit** 0.350 (1), **Đường tiệm cận** 0.529 (3), **Cực trị của hàm số**
  0.529 (3), **Thống kê** 0.650 (1), **Giới hạn và hàm số liên tục** 0.828 (3), **Thể tích khối chóp** 0.828 (3) →
  `enough_data: false`, `weak: false` → "Chưa đủ dữ liệu". The first two sit below 0.6 and would have been called weak
  before; the 0.529 ones would have read "Khá" on the old web bands.
- `POST /api/me/practice {"count": 20}` answered `groups: [{reason: "Chuyên đề yếu", topic: "Giá trị lớn nhất, nhỏ nhất",
  count: 20}]` — not one question was planned around a topic with fewer than five answers.
- `/me/stats` in the browser (http://localhost:8088) shows the same eight rows with "Cần ôn" on one and
  "Chưa đủ dữ liệu" on seven.

### AC-06 — decay on read and update, and a replay that reproduces it
Decay is toward 0.5 with a 60-day half-life, computed from `last_at` in `step()` (which now takes the answer's clock),
in `rollup()` and in the planner — never by a job.

`POST /api/analytics/mastery/rebuild` as `admin` answered `{"students": 4, "topics": 8, "facts": 77}` over the
organisation's 23 mastery rows. Run twice, the second replay was **byte-identical** to the first (23/23 rows). Against
the rows written *before* this feature, 13 of 23 moved, by at most **2.0e-05** — the one-time shift ADR-04 predicted, as
those values were accumulated without decay. A teacher and `buivanchau` both get **403**.

### AC-07 — a weekly snapshot exists
The bootstrap backfilled **23 rows** for the running business week (Mon 2026-09-21, Asia/Ho_Chi_Minh), 65 answers, mean
mastery 0.4919; the worker then wrote the same week again on start (`worker.mastery_week_snapshot rows=23`), replacing
rather than doubling. `GET /api/me/mastery/weekly` returns the series for `buivanchau` (8 topics, 20 answers in the
week); `GET /api/students/{id}/mastery/weekly` gives staff the same body, a student asking for another student gets
**403**, and staff on `/me/mastery/weekly` get **403**.

### T-03-04 — the silent gap is countable
`POST /api/questions/facets` now reports `topics["none"]`: **102** of the organisation's **377** questions carry no topic,
so they move no mastery and land in no report. The tagged subtree counts are unchanged.

### Checks
- `make lint-api` (ruff + 4 import contracts), `./scripts/verify.sh apps/api/tests`: **440 passed, 1 skipped**.
- `cd apps/web && pnpm typecheck`, `pnpm lint`, `pnpm test`: **174 passed** in 49 files.
- New tests: `tests/test_mastery_rebuild.py` (3) and `tests/test_mastery_weekly.py` (3); `test_mastery_api.py` — the
  thin topic and the weak one; `test_bank_facets.py` — questions with no topic; `tests/unit/test_analytics_handlers.py`
  — decay over a half-life, the weak rule with and without evidence, the replay and its 403s, the weekly snapshot,
  the job matching the backfill, the series' scoping, and a plan that refuses to build on two answers;
  `mastery.test.tsx` — the bands read the server's flags.
