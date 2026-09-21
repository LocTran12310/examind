---
feature: exam-practice
stories: 6
acceptance_criteria: 22
---

# Requirements — Exams, practice and statistics

## US-01 — Build an exam

As a teacher, I want to build an exam by hand or from a blueprint.

**Priority:** must

**AC-01** — Blueprint
```gherkin
Given usable questions in the bank
When I create an exam "Kiểm tra 15 phút" with rows (Đại số · mcq · 6), (Hình học · mcq · 4)
Then 10 distinct questions are drawn from those topic subtrees and grouped in section "Phần I"
And a row that cannot be filled reports "thiếu N câu"
```

**AC-02** — Manual edit
```gherkin
Given an exam
When I add questions from a bank search, remove one, reorder, or swap one for another random question of the same row
Then the exam's question list and total points update
```

**AC-03** — Scoring settings
```gherkin
Given an exam with MCQ, true/false and short-answer questions
When I open its settings
Then default points are 0.25 / 1 / 0.5 and I can change points per type or per question, and the total is shown
```

**AC-04** — Preview
```gherkin
Given an exam
When I open "Xem trước"
Then I see it exactly as students will (exam mode, no answers) and can toggle to show answers and solutions
```

## US-02 — Assign an exam

As a teacher, I want to assign an exam to classes with a time window.

**Priority:** must

**AC-05** — Create assignment
```gherkin
Given an exam and class "10A1"
When I assign it with open/close time, duration 45 minutes, 1 attempt, shuffle on, results "after submit"
Then every student of 10A1 sees it on their home page during the window
```

**AC-06** — Window enforcement
```gherkin
Given an assignment not yet open, or closed
When a student tries to start it
Then it is refused with the reason
```

## US-03 — Take an exam

As a student, I want to take an exam on any device with a timer and autosave.

**Priority:** must

**AC-07** — Start and timer
```gherkin
Given an open assignment
When I start it
Then I see the questions (shuffled if configured, answers hidden), a countdown to my deadline and a question navigator
```

**AC-08** — Autosave and resume
```gherkin
Given I answered some questions
When I reload the page or switch device
Then my answers and remaining time are restored
```

**AC-09** — Submit and auto-close
```gherkin
Given I click "Nộp bài" and confirm, or my time runs out
Then the attempt is finalised; answers sent after the deadline are refused
```

**AC-10** — Tab switches
```gherkin
Given I leave the exam tab during an attempt
When I come back
Then the switch is counted and visible to the teacher
```

## US-04 — Grading and results

As a student, I want my score and feedback right after submitting.

**Priority:** must

**AC-11** — Auto grading
```gherkin
Given a submitted attempt
Then MCQ, true/false (partial credit) and short answers are graded immediately and the total score is shown out of 10 (scaled)
```

**AC-12** — Result page
```gherkin
Given results policy "after submit"
When I open my result
Then each question shows my answer, the correct answer and the solution (QuestionView result mode)
And a breakdown by section and by topic
```

**AC-13** — Results policy
```gherkin
Given policy "after close" or "never"
When I open my result before the close time (or ever, for never)
Then I see only my total, without answers or solutions
```

**AC-14** — Essay grading
```gherkin
Given an attempt with essay answers
When the teacher enters points and a comment for each essay
Then the attempt total updates and the student sees the comment
```

**AC-15** — Snapshot integrity
```gherkin
Given a question edited after students answered it
When their results are shown
Then they keep the grade computed at submission; and the question cannot be deleted from the bank
```

## US-05 — Reports

As a teacher, I want to see where marks were lost.

**Priority:** must

**AC-16** — Assignment report
```gherkin
Given submitted attempts
When I open the assignment report
Then I see submitted/not-submitted students, average, score distribution, and per question % correct with the most chosen wrong option
```

**AC-17** — Topic tree stats
```gherkin
Given graded answers
When I open "Theo chuyên đề"
Then I see the knowledge tree with % correct at every level (roll-up of descendants), expandable
```

**AC-18** — Other dimensions
```gherkin
Given graded answers
When I group by tag, question type or difficulty
Then I see % correct and number of answers per group, filterable by class and date range
```

**AC-19** — Heatmap
```gherkin
Given a class
When I open the class heatmap
Then rows are students, columns are top-level topics (strands) or topics, cells are % correct coloured
```

## US-06 — Student home and stats

As a student, I want one place for my exams and progress.

**Priority:** must

**AC-20** — Home
```gherkin
Given assignments for my classes
When I open /home
Then I see "Đang mở", "Sắp tới" and "Đã làm" with scores
```

**AC-21** — My stats
```gherkin
Given my graded answers
When I open "Tiến độ của tôi"
Then I see my % correct by topic tree level and by type, weakest topics first
```

**AC-22** — Navigation
```gherkin
Given the growing number of pages
When staff use the app
Then navigation is a grouped sidebar (Đề & câu hỏi, Lớp & học sinh, Báo cáo, Cài đặt) that works on phones
```

## Non-functional

| Kind | Requirement | Verified by |
| --- | --- | --- |
| Performance | Report queries < 500 ms for 30 students × 40 questions × 20 exams | T-04-01 |
| Mobile | Exam page usable at 375 px | T-02-04 |
