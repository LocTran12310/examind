---
feature: 2026092301-learning-telemetry
environments: [local]
viewports: [desktop, mobile]
---

# Verification — Learning telemetry

This feature is mostly data: timing columns, item statistics, mastery rules and a weekly snapshot. Only the
statistics panel has a screen of its own, and since the clean-up of 2026-09-23 the bank holds **no graded
answers at all**, so what a browser can show is the honest half of AC-03: the panel exists, names its threshold
and refuses to invent numbers. The rest is listed below with the tests that cover it.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert |
|---|---|---|---|---|---|
| S1 | The bank opens a question | `/org/bank` | `settle 2500; click a[href^="/org/bank/"]:not([href$="/new"]) >> nth=0; settle 2500` | AC-03 | `text=Thống kê từ bài làm` |
| S2 | With no answers yet, the panel says so instead of showing a made-up number | `/org/bank` | `settle 2500; click a[href^="/org/bank/"]:not([href$="/new"]) >> nth=0; settle 2500; scroll text=Thống kê từ bài làm; settle 500` | AC-03 | `text=Chưa đủ dữ liệu`; `no-text=Không tải được` |

| S3 | One real answer reaches the teacher's report | `/org/reports` | `settle 2500` | AC-01 | `text=1 lượt`; `no-text=Không tải được` |
| S4 | The 21 blanks and the abandoned practice added nothing | `/org/reports` | `settle 2500; click [role=tab] >> nth=2; settle 1500` | AC-02 | `text=1 lượt`; `no-text=6 lượt` |

## Data setup

S3 and S4 read numbers a student had to produce, and the runner signs in as one account, so the answering half is
scripted: `apps/api/scripts/verify_student_answers.py` signs in as the student, answers **one** question of an
open assignment in 42 seconds and submits it (leaving 21 blank), then starts a practice attempt and abandons it.

That makes the assertions differential rather than decorative. One answer counted is AC-01. `no-text=6 lượt` is
AC-02: before this feature the abandoned practice's five questions would have been graded 0 and counted, so the
page would read six. The exact numbers are what the script produces; re-run it before re-running the steps.

## Not verified here

Nothing else in this feature reaches a screen, and the live bank has no graded answers to drive the parts that
would. Creating attempts to produce screenshots would put machine-made data back into the organisation that was
just cleaned, which is worse than a named gap.

| AC | Covered by |
| --- | --- |
| AC-04 search by observed difficulty | `tests/test_item_stats.py` |
| AC-05 one weak-topic rule | `tests/unit/test_analytics_handlers.py`, `tests/test_mastery_api.py`, `tests/test_adaptive.py`; seen live before the clean-up (7 of 8 topics read "Chưa đủ dữ liệu", the one with 5 answers read "Cần ôn") |
| AC-06 decay and recompute | `tests/test_mastery_rebuild.py` (replay reproduces the numbers) |
| AC-07 weekly snapshot | `tests/test_mastery_weekly.py` |

## Notes

S3 verifies AC-01 as far as a screen can: the answer the student gave is there and counted. The seconds and the
first-attempt flag have no screen at all — they are covered by `tests/test_attempts_api.py` (accumulates over two
saves, clamped to the attempt window), `tests/unit/test_assessment_handlers.py` and
`apps/web/src/__tests__/exam-runner.test.tsx`, and the script above sends 42 s so the stored value is checkable
in the database if anyone doubts the screenshot.

S1 and S2 verify AC-03 as far as an empty bank allows: the panel is there and it refuses to show numbers below ten
answers. The other half — the numbers themselves — is covered by `tests/test_item_stats.py` and was measured live
on 2026-09-23 before the clean-up: 67% correct, 75% at first attempt, discrimination +1.00, median 25 s.

To capture AC-01, AC-02 and the numeric half of AC-03 in a browser, one student attempt has to exist. That is a
deliberate decision about live data, not a technical limit: say so and the script grows two steps (take an
assigned attempt, leave a second one abandoned) with the data that implies.

The step clicks `a[href^="/org/bank/"]:not([href$="/new"])`: the first link under that prefix is "Thêm câu hỏi",
and a run that opens the new-question form instead of a question is green on nothing.
