# Adaptive review

## Problem
Scores tell a student *that* they are weak, not *what to do next*. Teachers cannot hand-build a
different review exam for each of 40 students. And a wrong answer key in the bank silently
punishes every student who answered correctly.

## Outcome
---
feature: adaptive-review
slug: 2026092204-adaptive-review
owner: Loc Tran
created: 2026-09-22
status: approved
---

## Success signal
For a student with graded answers, a generated review exam draws ≥ 60% of its questions from
their three weakest leaf topics and contains every question they answered wrong more than a
day ago (up to 10%); a seeded wrong answer key is flagged after the first class submits.

## Out of scope
- IRT/BKT models (planned upgrade; the MVP uses a difficulty-weighted moving average)
- LLM-generated question variants
- Push notifications / reminders

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Student | Re-reads everything before a test | Presses "Tạo đề ôn tập" and gets 20 questions aimed at their weakest topics, plus the ones they got wrong last week |
| Teacher | Assigns the same revision sheet to everyone | Assigns "đề ôn cá nhân" to a class: every student receives their own exam |
| Teacher | Discovers a wrong key only when a student complains | Sees questions flagged "Nghi sai đáp án" in the review queue, with the evidence |

## Constraints
| Kind | Detail |
| --- | --- |
| Cost | No model calls; everything is SQL + Python |
| Fairness | A flagged question is excluded from new exams until reviewed, never auto-rewritten |
| Consistency | Practice attempts reuse the exam runner, scoring and answer_facts |

## Existing surface touched
- Reused: `answer_facts`, `scoring`, `assignments.new_attempt`, `ExamRunner`, `ResultView`, review queue, `TopicStatsTree`
- New: `student_topic_mastery`, practice exams (`exams.source = adaptive`), flag detection job
- Entry points: `/me/stats` ("Tạo đề ôn tập"), `/org/classes/[id]` ("Giao đề ôn cá nhân"), review queue group "Nghi sai đáp án"
