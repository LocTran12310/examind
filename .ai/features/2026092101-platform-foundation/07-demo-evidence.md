# Demo evidence — platform-foundation

Run on 2026-09-22 against `docker compose up` (http://localhost:8088), Mac M-series (arm64). amd64 images built with `docker buildx --platform linux/amd64` (api + web, exit 0).

| UoW | Step | How verified |
| --- | --- | --- |
| UOW-01 | Stack healthy, `/api/health` ok | curl through Caddy |
| UOW-01 | system/admin login → forced password change → home | Browser (in-app) |
| UOW-01 | Wrong password → generic error | Browser |
| UOW-01 | Org code prefilled after reload | Browser (`system` prefilled) |
| UOW-01 | Refresh, logout, lockout, suspended org | pytest `test_auth_api.py`, `test_auth_service.py` |
| UOW-02 | Create TrungtamA → temp password shown once | Browser |
| UOW-02 | Duplicate `TRUNGTAMA`, suspend/activate/delete, system org guarded | pytest `test_orgs_api.py`; UI in vitest `orgs.test.tsx` |
| UOW-02 | trungtama/admin forced change | curl through Caddy |
| UOW-03 | Import `samples/students-30.csv` → 30 accounts in 10A1/10A2 | curl through Caddy (preview + commit) |
| UOW-03 | `samples/students-bad.csv` → rows 7, 9, 10 reported | curl through Caddy |
| UOW-03 | Imported student `buivanchau` forced to change password | Browser |
| UOW-03 | Users list with classes and statuses | Browser |
| UOW-03 | Create/edit/deactivate, reset, classes members | pytest `test_users_api.py`, `test_classes_api.py`; vitest `users/import/classes.test.tsx` |
| UOW-04 | Toán tree shown with levels and grades | Browser |
| UOW-04 | Add/rename/move/merge/delete guard | pytest `test_topics_api.py`; vitest `TopicTree.test.tsx` |
| UOW-04 | Tags CRUD + duplicate refused | pytest `test_tags_api.py`; vitest `tags.test.tsx` |
| UOW-04 | `/dev/question-preview`: KaTeX, image in option C, solution with image, answer | Browser (screenshot); exam-mode hiding in vitest `QuestionView.test.tsx` |

Test totals at close: API 55 passed, web 29 passed, `tsc` clean, `eslint` clean.
Dev credentials after the demo: `system/admin/admin123456`, `trungtama/admin/admin123456`.
