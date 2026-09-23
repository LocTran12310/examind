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

## Not verified here

Nothing else in this feature reaches a screen, and the live bank has no graded answers to drive the parts that
would. Creating attempts to produce screenshots would put machine-made data back into the organisation that was
just cleaned, which is worse than a named gap.

| AC | Covered by |
| --- | --- |
| AC-01 seconds, first-seen and first-attempt recorded | `tests/test_attempts_api.py` (accumulates over two saves, clamped to the window), `tests/unit/test_assessment_handlers.py`, `apps/web/src/__tests__/exam-runner.test.tsx` (the body carries the seconds, revisiting a question adds to them) |
| AC-02 an unanswered question leaves no fact | `tests/test_attempts_api.py` (a swept attempt writes no facts and no mastery), `tests/unit/test_assessment_handlers.py` |
| AC-04 search by observed difficulty | `tests/test_item_stats.py` |
| AC-05 one weak-topic rule | `tests/unit/test_analytics_handlers.py`, `tests/test_mastery_api.py`, `tests/test_adaptive.py`; seen live before the clean-up (7 of 8 topics read "Chưa đủ dữ liệu", the one with 5 answers read "Cần ôn") |
| AC-06 decay and recompute | `tests/test_mastery_rebuild.py` (replay reproduces the numbers) |
| AC-07 weekly snapshot | `tests/test_mastery_weekly.py` |

## Notes

S1 and S2 verify AC-03 as far as an empty bank allows: the panel is there and it refuses to show numbers below ten
answers. The other half — the numbers themselves — is covered by `tests/test_item_stats.py` and was measured live
on 2026-09-23 before the clean-up: 67% correct, 75% at first attempt, discrimination +1.00, median 25 s.

To capture AC-01, AC-02 and the numeric half of AC-03 in a browser, one student attempt has to exist. That is a
deliberate decision about live data, not a technical limit: say so and the script grows two steps (take an
assigned attempt, leave a second one abandoned) with the data that implies.

The step clicks `a[href^="/org/bank/"]:not([href$="/new"])`: the first link under that prefix is "Thêm câu hỏi",
and a run that opens the new-question form instead of a question is green on nothing.
