---
feature: ui-standards
stories: 5
acceptance_criteria: 6
---

# Requirements

## US-01 — No silent duplicate uploads
**Priority:** must

**AC-01** — Choose per file
```gherkin
Given files already uploaded (same content) or with the name of an uploaded document
When I pick them in the upload form
Then each shows what it matches and a choice (skip / re-parse; replace / keep both / skip), skipped files are not sent, the same content is never stored twice
```

## US-02 — Filter operators
**Priority:** must

**AC-02** — Operators
```gherkin
Given a list with text, number and date filters
When I pick an operator from the symbol menu next to a filter
Then the URL carries `<col>_op`, the server applies it (unknown operator → 422), and dates also offer a range
```

## US-03 — Business time zone
**Priority:** must

**AC-03** — Display and day filters
```gherkin
Given a timestamp 2026-09-21T17:30Z
When it is shown or a list is filtered on 22/09/2026
Then it shows 22/09/2026 00:30 and matches that day, in any browser or server zone
```

## US-04 — Exam order saved once
**Priority:** must

**AC-04** — Draft ordering
```gherkin
Given an exam
When I choose "Sắp xếp thứ tự", swap câu 1 with câu 3, move one down, then save
Then nothing is saved until "Lưu thứ tự", one request carries the whole order, and moves stay inside a part
```

## US-05 — Consistent shadcn UI
**Priority:** should

**AC-05** — No raw controls
```gherkin
Given the app pages and components
When they render buttons, inputs, labels, tables, collapsibles or keys
Then they use the shadcn components (raw tags only inside asChild)
```

**AC-06** — Preview fills the dialog
```gherkin
Given the exam preview dialog maximised
When it renders
Then the questions fill the dialog and scroll inside it, without an empty band
```
