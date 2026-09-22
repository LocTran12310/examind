---
id: UOW-02
slug: back-and-editor
title: Back keeps list state; topic tree and ⌘+Enter in the question editor
demoable: true
duration: 2d
depends_on: []
requirements: [US-03, US-04]
verifies: [AC-03, AC-04, AC-05]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Back keeps list state; topic tree and ⌘+Enter in the question editor

## Demo script
1. Bank page 2 + filter → open a question → ← returns to page 2
2. Sửa câu → Chọn chuyên đề shows the tree → pick → ⌘ Enter saves

## In scope
- list-memory + BackLink
- TopicTreePick
- useSaveShortcut

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-03, AC-04, AC-05 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
