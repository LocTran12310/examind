---
feature: topic-coverage
stories: 3
acceptance_criteria: 5
---

# Requirements

## US-01 — Find and clear the backlog
**Priority:** must

**AC-01** — The queue
```gherkin
Given questions with no topic in my organisation
When I open "Chưa gắn chuyên đề"
Then I see them newest first with their subject and source document, the count remaining, and I can filter by document and subject
```

**AC-02** — Suggestions
```gherkin
Given a question in the queue
When it is shown
Then up to three suggested topics appear with their score and origin (từ khóa / tương tự), and choosing one assigns it as the primary topic and removes the question from the queue
```

**AC-03** — Bulk apply
```gherkin
Given several questions I have selected
When I apply a topic to them
Then all of them get it as primary topic in one request and the remaining count drops accordingly
```

## US-02 — The backlog stops refilling
**Priority:** must

**AC-04** — Untagged means review
```gherkin
Given a document whose questions the classifier cannot place
When ingestion stores them
Then they are needs_review with the reason "chưa gắn chuyên đề", never auto_approved, and they appear in the tagging queue
```

## US-03 — Progress is visible
**Priority:** should

**AC-05** — Coverage
```gherkin
Given the bank of a subject
When I look at the tagging queue or the bank facets
Then I see how many questions have no topic and how many of them are from each document
```
