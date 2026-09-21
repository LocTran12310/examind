---
feature: question-review
stories: 6
acceptance_criteria: 20
---

# Requirements — Question review and bank

## US-01 — Automatic triage

As a teacher, I want confident questions approved automatically and the rest queued, so I only look at what is likely wrong.

**Priority:** must

**AC-01** — Triage on ingestion
```gherkin
Given a parsed document and my org threshold 0.85
When questions are stored
Then questions with confidence ≥ 0.85, an answer and no blocking issue become "auto_approved"
And the others become "needs_review", each with its issues
```

**AC-02** — Document progress
```gherkin
Given a triaged document
When I open /org/review
Then each document shows counts: tự duyệt, cần xem, đã duyệt, loại, trùng — and a progress bar
```

**AC-03** — Near-duplicates
```gherkin
Given a question nearly identical (same type, similarity ≥ 0.9) to a usable question in my org
When it is ingested
Then it becomes "duplicate" linked to the existing question, and I can restore it with one click
```

## US-02 — Keyboard review queue

As a teacher, I want to review flagged questions one by one with single keys.

**Priority:** must

**AC-04** — Queue order and grouping
```gherkin
Given a document with flagged questions
When I open its review queue
Then I see one question at a time, grouped by issue ("thiếu đáp án" first), with a counter "2/5"
And for PDF/scan documents the source page image is shown beside it
```

**AC-05** — Single-key actions
```gherkin
Given a question is focused in the queue
When I press 1–4 the MCQ answer becomes A–D (a–d toggles a true/false statement)
And Enter approves and moves to the next, X rejects, J/K move, S skips, T opens topic search, E edits
Then each change is saved immediately without a Save button
```

**AC-06** — One-touch suggestions
```gherkin
Given a question with a suggested topic and (for AI results) a suggested answer
When the queue shows it
Then the suggestion is pre-selected and Enter accepts it
```

**AC-07** — Inline edit
```gherkin
Given I press E
When I edit stem, options, answer or solution in Markdown with live KaTeX preview and press Ctrl+Enter
Then the question is saved, its issues recomputed, and I stay on it
```

## US-03 — Bulk actions

As a teacher, I want to fix many questions at once.

**Priority:** must

**AC-08** — Approve all confident
```gherkin
Given a document with auto_approved questions
When I click "Duyệt tất cả câu tin cậy cao"
Then they all become approved
```

**AC-09** — Paste answer key
```gherkin
Given MCQ questions without answers
When I paste "1A 2C 3B" (or "1.A, 2.C" or one letter per line)
Then answers are set by number, questions whose only issue was the missing answer move to approved-ready, and a summary shows how many were applied
```

**AC-10** — Bulk edit
```gherkin
Given I select several questions in the document list
When I set topic, difficulty or tags for the selection
Then all selected questions are updated in one request
```

## US-04 — Quality loop

As a center admin, I want the system to check itself and learn from corrections.

**Priority:** should

**AC-11** — Spot checks
```gherkin
Given auto-approved questions in a document
When the document is triaged
Then 5% (at least 1) of them are queued as "Kiểm tra ngẫu nhiên"
And if 2 of the last 20 spot checks were rejected or edited, the org threshold rises by 0.05 (max 0.95)
```

**AC-12** — kNN topic suggestion
```gherkin
Given approved questions with confirmed topics
When a similar new question is ingested and keyword matching is weak
Then its suggested topic comes from the most similar approved question (source "knn")
```

**AC-13** — Review events
```gherkin
Given any review action (approve, reject, edit, answer, topic)
When it happens
Then a review event (user, question, action, before/after) is recorded for the quality metrics
```

## US-05 — Team workflow

As a center admin, I want to split review work between teachers.

**Priority:** could

**AC-14** — Assign documents
```gherkin
Given several documents need review
When I assign a document to a teacher
Then it appears under "Của tôi" in that teacher's review list
```

## US-06 — Question bank

As a teacher, I want to find, create and edit questions in one bank.

**Priority:** must

**AC-15** — Search and filter
```gherkin
Given approved questions across subjects, grades and topics
When I search "parabol" with filters grade 10, topic "Hàm số bậc hai và đồ thị" (subtree), status usable
Then I see matching questions paginated with their topic, tags, difficulty and status
```

**AC-16** — Topic subtree
```gherkin
Given questions tagged to leaf "Tìm đỉnh và trục đối xứng parabol"
When I filter by its parent "Hàm số bậc hai và đồ thị" or grand-parent "Đại số"
Then those questions are included
```

**AC-17** — Edit a question
```gherkin
Given a question in the bank
When I edit stem, options, answer, solution, difficulty, topics (one primary) and tags, and upload an image into the stem
Then the changes are saved and rendered by QuestionView
```

**AC-18** — Create manually
```gherkin
Given I click "Thêm câu hỏi"
When I fill a new MCQ with an image and save
Then it is created as approved with source "manual"
```

**AC-19** — Delete and restore
```gherkin
Given a question not used by any exam
When I delete it
Then it is removed (rejected questions can be restored from the "Đã loại" filter)
```

**AC-20** — Permissions and isolation
```gherkin
Given a student or a user of another org
When they call bank or review endpoints
Then they get 403 or 404
```

## Non-functional

| Kind | Requirement | Verified by |
| --- | --- | --- |
| Performance | Bank search < 300 ms for 10 000 questions (trigram + ltree indexes) | T-04-01 |
| UX | Review flow for the golden docs: ≤ 15% flagged, ≤ 2 actions per flagged question | T-02-04 |
