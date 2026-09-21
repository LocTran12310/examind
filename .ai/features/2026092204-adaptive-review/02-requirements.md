---
feature: adaptive-review
stories: 4
acceptance_criteria: 12
---

# Requirements — Adaptive review

## US-01 — Mastery per topic

As a student and teacher, I want a mastery level per topic that follows recent performance.

**Priority:** must

**AC-01** — Update on grading
```gherkin
Given a student answers questions tagged to leaf topics
When the attempt is graded (and when an essay is graded later)
Then the student's mastery for each leaf topic is updated with the difficulty-weighted moving average
```

**AC-02** — Read mastery
```gherkin
Given mastery rows exist
When the student opens "Tiến độ của tôi" or a teacher opens the student's page
Then they see mastery per leaf and rolled up to parents, weakest first, with the number of answers
```

**AC-03** — Backfill
```gherkin
Given answer facts that existed before mastery tracking
When the backfill command runs
Then mastery equals what incremental updates would have produced in chronological order
```

## US-02 — Personal review exam (student)

As a student, I want one button that builds a review exam for me.

**Priority:** must

**AC-04** — Composition
```gherkin
Given my mastery and answer history
When I press "Tạo đề ôn tập"
Then I get 20 questions: ~60% from my 3 weakest topics, ~30% from medium topics, up to 10% re-asks of questions I got wrong ≥ 24 h ago
And difficulty follows my mastery, and I never get questions I answered correctly in the last 7 days or flagged questions
```

**AC-05** — Take and see results
```gherkin
Given the review exam
When I take it
Then it uses the normal exam page (60-minute cap) and shows results immediately, and my mastery updates
```

**AC-06** — No history
```gherkin
Given I have no graded answers yet
When I press "Tạo đề ôn tập"
Then I get a balanced exam across strands of my grade and a note that it will adapt after this one
```

## US-03 — Personal review exams for a class (teacher)

As a teacher, I want to give every student in a class their own review exam at once.

**Priority:** should

**AC-07** — Assign to class
```gherkin
Given class 10A1 with graded students
When I click "Giao đề ôn cá nhân" with 15 questions, a window and 30 minutes
Then each student gets their own exam and assignment, visible on their home page
```

**AC-08** — Overview
```gherkin
Given personal review assignments
When I open the class page
Then I see each student's weakest topics and review assignment status
```

## US-04 — Suspect answer keys

As a teacher, I want the system to catch wrong answer keys from student behaviour.

**Priority:** must

**AC-09** — Detect
```gherkin
Given a MCQ with ≥ 10 graded answers where the best students mostly chose another option
When detection runs
Then the question becomes "flagged" with issue "Nghi sai đáp án" and evidence (option counts, top-quartile choice)
```

**AC-10** — Review flagged questions
```gherkin
Given flagged questions
When I open the review list
Then their documents show "Nghi sai đáp án" counts, the queue shows the evidence, and fixing the key (1–4) + Enter approves it
```

**AC-11** — Exclusion
```gherkin
Given a flagged question
When exams are generated (blueprint or adaptive)
Then it is not drawn until approved again
```

**AC-12** — No false alarm on hard questions
```gherkin
Given a hard question where the best students chose the key and weaker students spread across options
When detection runs
Then it is not flagged
```

## Non-functional

| Kind | Requirement | Verified by |
| --- | --- | --- |
| Performance | Generating a review exam < 500 ms with 10 000 questions and 50 000 facts | T-02-01 |
