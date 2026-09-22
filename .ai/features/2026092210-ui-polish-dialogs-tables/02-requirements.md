---
feature: ui-polish-dialogs-tables
stories: 5
acceptance_criteria: 6
---

# Requirements — Dialogs, tables, navigation, small screens

## US-01 — Resizable dialogs
**Priority:** must

**AC-01** — Maximise and resize
```gherkin
Given a form dialog is open
When I press "Phóng to" (or double-click its title), then drag its right, left or bottom edge or a corner
Then it fills the window, returns with "Thu nhỏ", and follows the drag within the window
```

## US-02 — Readable tables
**Priority:** must

**AC-02** — Borders and zebra rows
```gherkin
Given any DataTable list
When it renders
Then columns are separated by borders, even rows have a tinted background, and the header plus filter row stay on top while the body scrolls
```

## US-03 — Back keeps the list state
**Priority:** must

**AC-03** — Same page and filters
```gherkin
Given page 2 of a list with a filter
When I open a row's detail page and press its "←" link (or Hủy / after creating)
Then I am back on page 2 with the same filter and sort
```

## US-04 — Question editor
**Priority:** must

**AC-04** — Topic tree
```gherkin
Given I edit a question
When I press "Chọn chuyên đề"
Then I see the subject's topic tree with search, and choosing a node sets it as the primary topic
```

**AC-05** — ⌘ + Enter
```gherkin
Given the question editor on a Mac (also while typing Vietnamese)
When I press ⌘ + Enter
Then the question is saved; the button shows "⌘ Enter" on Apple devices and "Ctrl + Enter" elsewhere
```

## US-05 — Compact spacing
**Priority:** should

**AC-06** — Small screens
```gherkin
Given a screen narrower than 640 px
When a list page is shown
Then the page padding is at most 8 px and the header/table gaps are reduced, larger screens keep moderate spacing
```
