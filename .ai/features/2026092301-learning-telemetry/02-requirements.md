---
feature: learning-telemetry
stories: 4
acceptance_criteria: 7
---

# Requirements

## US-01 — Answers carry their own evidence
**Priority:** must

**AC-01** — Timing and attempt number
```gherkin
Given a student answering a question in an exam or practice
When the answer is saved and later graded
Then attempt_answers and answer_facts carry seconds_spent, first_seen_at and whether it was the first attempt at that question, and seconds_spent never exceeds the attempt window
```

**AC-02** — Unanswered questions do not count
```gherkin
Given an attempt submitted by the student or closed by the expiry sweep
When questions were never answered
Then they are scored 0 for the exam result as before, but they produce no answer fact, do not move mastery and are excluded from item statistics
```

## US-02 — Item statistics a teacher can act on
**Priority:** must

**AC-03** — Statistics per question
```gherkin
Given a question answered by at least 10 students
When a teacher opens it
Then it shows share correct, share correct at first attempt, discrimination between the strongest and weakest third, median seconds and, for a multiple choice question, how many chose each option; with fewer observations it says "chưa đủ dữ liệu"
```

**AC-04** — The bank can be searched by them
```gherkin
Given the question search
When filtering or sorting on share correct or number of observations
Then the server answers with the same search contract as every other list
```

## US-03 — Mastery that can be trusted
**Priority:** must

**AC-05** — One definition of weak, with enough evidence
```gherkin
Given a student's mastery rows
When the planner, the API or a report names a weak topic
Then all three use mastery < 0.6 with at least 5 answers, and topics below that answer count are reported as "chưa đủ dữ liệu" instead of weak
```

**AC-06** — Decay and recompute
```gherkin
Given a topic with no answers for 60 days
When mastery is read or updated
Then it has moved halfway back toward 0.5, and POST /analytics/mastery/rebuild replays the facts to reproduce the same numbers
```

## US-04 — A trend exists
**Priority:** should

**AC-07** — Weekly snapshot
```gherkin
Given a student with answers in several weeks
When the weekly job has run (or the backfill for past weeks)
Then one row per student, topic and week holds the mastery at the end of that week and the answers in it, and an API returns the series for a student
```
