# Exams, practice and statistics

## Problem
A question bank only pays off when teachers can turn it into exams in minutes, students can
take them online, and everyone sees *where* marks were lost — per topic at every level of the
knowledge tree ("Giải tích 72% › Nguyên hàm 58% › Từng phần 31%"), per tag and per question type.

## Outcome
---
feature: exam-practice
slug: 2026092203-exam-practice
owner: Loc Tran
created: 2026-09-22
status: approved
---

## Success signal
A teacher builds a 40-question exam from a blueprint and assigns it to a class in < 3 minutes;
a student's submission is graded instantly (MCQ/true-false/short answer) and the class report
shows correctness by topic level, tag and type within one second of submission.

## Out of scope
- Mastery model and personalised review exams (feature `adaptive-review`)
- Proctoring beyond tab-switch logging
- Exporting printable Word/PDF exams with multiple versions (post-MVP)
- Payments, parent accounts

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher | Copies questions into Word, prints, grades by hand | Builds an exam from a blueprint in one screen, assigns it to a class, sees results by topic |
| Student | Paper exams, a single final score | Takes the exam on phone/PC with a timer, sees per-question feedback and solutions, and a topic breakdown |
| Center admin | — | Compares classes on the same exam |

## Constraints
| Kind | Detail |
| --- | --- |
| Scoring | Default THPT 2025 rules: MCQ 0.25, true/false 1.0 with partial credit 0.1/0.25/0.5/1, short answer 0.5; configurable per exam |
| Integrity | Server is the clock: answers after the deadline are refused, attempts auto-close |
| Devices | Exam page usable on a 375 px phone |

## Existing surface touched
- Reused: bank search (`bank.search`), `QuestionView` (exam/result modes), topic tree (`ltree`), tags, classes, `TopicPicker`
- New: exams, exam_questions, assignments, attempts, attempt_answers, answer_facts; student home; reports
- Entry points: `/org/exams`, `/org/exams/[id]`, `/org/assignments/[id]`, `/home`, `/exam/[attemptId]`, `/results/[attemptId]`, `/me/stats`
