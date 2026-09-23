---
feature: pickers-builder
stories: 4
acceptance_criteria: 7
---

# Requirements

## US-01 — The picker starts where the system already guessed
**Priority:** must

**AC-01** — Opens on the suggestion
```gherkin
Given a question whose suggestions are on screen
When I open the topic picker with `T` or with "Chuyên đề khác…"
Then the suggested topic is expanded, focused and ready to confirm, and nothing has been applied yet
```

**AC-02** — Counts are questions
```gherkin
Given any topic picker
When it lists topics
Then the number beside a topic is how many usable questions that subtree holds for the subject in hand, a topic with none reads 0, and the count of child topics is not shown as a number
```

## US-02 — A page of the tagging queue can be cleared in one click
**Priority:** must

**AC-03** — Take each row's own suggestion
```gherkin
Given several selected questions, each with its own suggestion
When I choose "Gán theo gợi ý"
Then each question gets its own top suggestion in one request, questions without one are left untouched and named, and the remaining count drops by what was applied
```

**AC-04** — Long filters behave
```gherkin
Given the document filter with more options than fit
When I open it
Then the list scrolls inside the dropdown and loads further pages as I reach the end
```

## US-03 — The bank can classify what it holds
**Priority:** must

**AC-05** — Subject and grade in bulk
```gherkin
Given questions selected in the bank, including the "Chưa phân môn" tab
When I set a subject or a grade for them
Then one request applies it, the list refreshes and the tab counts follow
```

## US-04 — The builder refuses to lie
**Priority:** must

**AC-06** — No silent empty row
```gherkin
Given a blueprint row on a topic with no usable question
When I generate the exam
Then it is refused with a message naming that topic and how many questions it holds, instead of returning fewer questions than asked
```

**AC-07** — Swap by hand
```gherkin
Given a question in an exam
When I choose to swap it
Then I can either let the system pick a replacement as today, or search the bank and choose one myself, and the exam keeps its points and order
```
