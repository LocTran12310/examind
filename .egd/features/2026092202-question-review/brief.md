# Question review and bank

## Problem
Ingestion produces drafts, but a bank only becomes trustworthy after a teacher confirms each
question — and at 40 questions per exam, per teacher, per week, that confirmation must cost
seconds, not minutes. Teachers should only look at questions that are likely wrong, fix each
with one key, and trust that everything else was filed correctly.

## Outcome
---
feature: question-review
slug: 2026092202-question-review
owner: Loc Tran
created: 2026-09-22
status: approved
---

## Success signal
On the golden set, a teacher gets a 40-question exam into the bank in < 10 minutes with
≤ 15% of questions in "Cần xem" and ≤ 2 actions on average per reviewed question
(measured by the review-flow test replaying the golden documents).

## Out of scope
- Building exams from the bank, student attempts (feature `exam-practice`)
- "Suspect answer key" from student statistics (feature `adaptive-review`)
- Pixel-accurate crops of each question from the source page (whole source page is shown for PDFs/scans)
- Embedding models for dedupe/kNN (pg_trgm similarity is used instead; embeddings can replace it later)

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher | Would re-read all 40 parsed questions | Reviews only the flagged ~15%, keyboard-only, then searches the bank by topic |
| Center admin | — | Sets the auto-approve threshold; sees review progress per exam and spot-check quality |

## Constraints
| Kind | Detail |
| --- | --- |
| Cost | No model required: triage, dedupe and kNN run in Postgres |
| UX | Every review action reachable by a single key; autosave |
| Data | Approved questions are never modified by re-parsing |

## Existing surface touched
- Reused: `Question`, `QuestionTopic`, `QuestionTag`, `QuestionView`, `TopicTree` data, ingestion pipeline hooks (`POST_PERSIST`), `ParsedQuestionCard`
- New: review queue API/UI, bank API/UI, `review_events`, pg_trgm
- Entry points: `/org/review`, `/org/review/[documentId]`, `/org/bank`, `/org/bank/[id]`
