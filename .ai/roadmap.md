# Examind roadmap

Features run sequentially; each passes G0 → G5 before the next is opened.
Source plan: approved in chat 2026-09-21 (Loc Tran).

| # | Feature | Scope |
|---|---|---|
| 1 | `platform-foundation` | Compose stack, org-code login, RBAC, org CRUD, users + CSV import, classes, topic tree (ltree) + tags, `QuestionView` |
| 2 | `exam-ingestion` | Upload docx/pdf/scan → parse → rule-based splitter (stem/options/answer/solution/images) → LLM fallback; `ai_models` registry, model choice at upload |
| 3 | `question-review` | Confidence triage, auto-approve, keyboard review queue, answer-key paste, bulk actions, dedupe, question bank CRUD |
| 4 | `exam-practice` | Exam builder (manual + blueprint by topic/tag), assignments, taking exams, auto grading, results + solutions, stats by topic level/tag/type |
| 5 | `adaptive-review` | Topic mastery, personalised review exams, "suspect answer key" flags |

MVP success signal (features 2+3): a teacher gets a 40-question exam into the bank (upload + review) in < 10 minutes, with ≤ 15% of questions needing review.
