---
feature: bulk-safety
stories: 4
acceptance_criteria: 7
---

# Requirements

## US-01 — A bulk edit can be taken back at once
**Priority:** must

**AC-01** — Undo from the toast
```gherkin
Given I set a difficulty, a subject, a grade, a topic or a tag on selected questions
When the toast appears and I press "Hoàn tác"
Then every question that edit touched goes back to exactly what it was, the list refreshes, and the toast says how many were restored
```

**AC-02** — All or nothing
```gherkin
Given a batch of questions to restore
When one of them can no longer be restored
Then nothing is restored, and the refusal names the questions in the way
```

## US-02 — A mistake found later can still be found and undone
**Priority:** must

**AC-03** — Recent changes
```gherkin
Given bulk edits made in this organisation
When I open "Thay đổi gần đây"
Then I see one row per edit — when, who, what fields changed, how many questions — newest first, and each row can be undone
```

**AC-04** — An undo is part of the history
```gherkin
Given a batch I have undone
When I look at the list again
Then the undo is itself a row, the original row says it was undone, and neither offers undo again
```

**AC-05** — Old enough is read-only
```gherkin
Given a batch older than the undo window
When I look at it in the list
Then it is readable and says why it can no longer be undone
```

## US-03 — The toolbar says what it is about to change
**Priority:** should

**AC-06** — The count is on the action
```gherkin
Given questions selected in the bank
When I open a bulk action
Then the action names how many questions it will change, and with nothing selected it stays disabled
```

## US-04 — Every detail page has a way back
**Priority:** must

**AC-07** — Back links
```gherkin
Given the assignment report, the attempt result, the new-question form or the question preview
When the page is open
Then a back link leads to the list it belongs to, in the same place and shape as the other detail pages
```
