---
feature: review-ux
stories: 3
acceptance_criteria: 6
---

# Requirements

## US-01 — The list says what to do next
**Priority:** must

**AC-01** — One state, filterable
```gherkin
Given the review list
When I look at a document
Then it shows one state (Cần xem / Đang duyệt / Xong) with how many questions still wait, and I can filter and sort by that state
```

**AC-02** — The sample explains itself
```gherkin
Given a document with questions drawn for the check sample
When I read its row
Then the label says "Mẫu kiểm chứng" and one sentence explains it is 5% of the auto-approved questions, drawn to catch a wrong automatic decision
```

## US-02 — Every question stays reachable
**Priority:** must

**AC-03** — Filter by state on the document
```gherkin
Given a document being reviewed
When I open it
Then I see its questions filtered to "Cần xem" by default and can switch to Đã duyệt, Đã loại, Trùng or Tất cả
```

**AC-04** — Correct and re-decide
```gherkin
Given a question I already approved
When I open it from the document, edit its stem, options, key or solution and approve or reject it again
Then the change is saved, its state changes accordingly and the counts of the document follow
```

**AC-05** — The decision is obvious
```gherkin
Given a question on the review page
When it is shown
Then its current state is named on the row, and the action that changes it says what it will do
```

## US-03 — Points are where a teacher looks
**Priority:** should

**AC-06** — The exam states its weighting
```gherkin
Given an exam built from a document
When I open it
Then it shows the points of each part and the total, says how that maps to the 10-point scale, and the per-question points are editable from that same place
```
