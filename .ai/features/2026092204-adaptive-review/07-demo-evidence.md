# Demo evidence — adaptive-review

Run 2026-09-22 on the compose stack, org TrungtamA, class 10A1.

| UoW | Step | Result | How |
| --- | --- | --- | --- |
| UOW-01 | "Tiến độ của tôi": mastery weakest first (Tìm đỉnh parabol 17%, Hệ thức lượng 25%, …) | as specified | Browser screenshot |
| UOW-01 | Mastery backfilled on API boot for answers graded before the feature (6 rows) | as specified | psql count + pytest `test_mastery.py` |
| UOW-01 | EMA values, backfill = incremental | as specified | pytest |
| UOW-02 | "Tạo đề ôn tập" → 20-question exam, 60-minute cap, first question from a weak topic (Tập hợp) | as specified | Browser screenshot |
| UOW-02 | Composition (≥ 11/20 from weak topics or neighbours, 10% re-asks), exclusions, < 500 ms with 10k questions + 50k facts | as specified | pytest `test_adaptive.py` |
| UOW-02 | Class 10A1 → "Giao đề ôn cá nhân" → 15 personal exams created in 86 ms; overview lists weakest topics and "Chưa làm" | as specified | API + browser screenshot |
| UOW-03 | Wrong key seeded, 11 students answer → audit flags it with evidence; excluded from exams; fix + Enter approves; no re-flag | as specified | pytest `test_key_audit.py` |
| UOW-03 | Hard-but-correct question not flagged | as specified | pytest |
| UOW-03 | Review list badge + evidence panel in queue | as specified | vitest `flagged.test.tsx` |

Finding fixed during the demo: mastery was empty for answers graded before the feature → API boot backfills when the table is empty.
Test totals at close: API 200 passed, web 84 passed.
