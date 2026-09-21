# Demo evidence — exam-practice

Run 2026-09-22 on the compose stack, org TrungtamA, class 10A1 (15 imported students).

| UoW | Step | Result | How |
| --- | --- | --- | --- |
| UOW-01 | Blueprint (Đại số · MCQ · 6) + (Hình học · MCQ · 4) → 10 distinct questions, 2.5 points | as specified, no shortfall | API on stack; pytest `test_exams_api.py` |
| UOW-01 | Shortfall warning, swap/remove/reorder/points, bank delete refused for used questions | as specified | pytest; vitest `exam-builder.test.tsx` |
| UOW-01 | Grouped sidebar (staff), drawer on phones, minimal student bar | as specified | Browser screenshot; vitest `nav.test.tsx` |
| UOW-02 | Assign to 10A1 (15 students); student home shows "Đang mở" → Bắt đầu | as specified | API + browser |
| UOW-02 | Exam page: server countdown, navigator, autosave "Đã lưu", reload restores answers (1, 2) and time | as specified | Browser |
| UOW-02 | Submit with confirm → result page | 2/10 shown instantly | Browser |
| UOW-02 | Window, attempt limit, late answers 409, lazy + swept expiry, tab switches | as specified | pytest `test_assignments_api.py`, `test_attempts_api.py`; vitest `ExamRunner.test.tsx` |
| UOW-03 | Result: per-question feedback, sections, topics weakest-first | as specified | Browser screenshot |
| UOW-03 | after_close / never policies, essay grading, snapshot integrity | as specified | pytest `test_results_api.py`; vitest `result.test.tsx` |
| UOW-04 | Assignment report: 1/15 submitted, average 2, distribution, student list | as specified | Browser screenshot |
| UOW-04 | Topic roll-up equals descendant sums; groups; heatmap; students see only themselves; 24k facts < 1 s | as specified | pytest `test_stats_api.py` |

Findings fixed during the demo: shuffled options kept their original labels (C, B, D, A) → options are relabelled A–D
per attempt and mapped back to the original key when saving and grading (ADR-06); PDF text kept Word's combining
arrow (n⃗) which fonts render as a box → normalised to `$\vec{n}$` at extraction (questions parsed earlier keep the glyph).
Test totals at close: API 186 passed, web 77 passed.
