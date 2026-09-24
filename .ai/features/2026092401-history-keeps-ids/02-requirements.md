---
feature: history-keeps-ids
stories: 2
acceptance_criteria: 3
---

# Requirements

## US-01 — A deleted question leaves its history intact
**Priority:** must

**AC-01** — The id survives the deletion
```gherkin
Given a question with events in the history
When the question is deleted
Then every one of its events keeps the question's id, and the deletion itself still succeeds
```

**AC-02** — Old rows stay readable
```gherkin
Given events whose question id was already nulled before this change
When the history is read or an undo is attempted
Then they behave exactly as they do today, and nothing pretends to know which question they were about
```

## US-02 — A refusal names what it cannot restore
**Priority:** must

**AC-03** — The questions are named
```gherkin
Given a batch one of whose questions has since been deleted
When I undo it
Then the whole batch is refused and the refusal carries the ids it could not put back
```
