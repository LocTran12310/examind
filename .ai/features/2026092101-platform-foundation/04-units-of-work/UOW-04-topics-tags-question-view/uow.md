---
id: UOW-04
slug: topics-tags-question-view
title: Topic tree, tags and full question rendering
demoable: true
duration: 2d
depends_on: [UOW-02]
requirements: [US-06, US-07]
verifies: [AC-21, AC-22, AC-23, AC-24]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Topic tree, tags and full question rendering

## Demo script
1. Log in as a teacher of trungtama, open /org/topics
2. Expand Giải tích › Nguyên hàm, add 'Nguyên hàm từng phần', rename it, move it under Tích phân and back
3. Try deleting 'Nguyên hàm' → refused; merge a test node into another → children moved
4. Open /org/tags, create 'đổi biến' in Phương pháp, rename, try a duplicate → refused, delete
5. Open /dev/question-preview → sample question renders KaTeX, image in option C, solution with image; toggle exam mode hides answer and solution

## In scope
- Topic service (create/rename/move/merge/delete) and tag API
- Assets in MinIO + minimal question model + demo question seed
- Topic tree UI, tags UI, QuestionView component + preview page

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-21, AC-22, AC-23, AC-24 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
