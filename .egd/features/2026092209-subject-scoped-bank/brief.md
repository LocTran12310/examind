# Question bank filtered by subject first

## Problem
The bank shows one flat row of filters for every subject at once: the topic tree mixes Đại số with
Hoá and Lý, the tag list has every tag of the org, and nothing tells the teacher how many questions a
choice will leave. Loc Tran (chat, 2026-09-22): "Bộ lọc nên phân theo từng môn không? chuyên đề, tags,
... chuyên đề của đại số không hề liên quan đến hoá, lý. nên để bộ lọc filter dropdown dialog hay đại
loại thế."

## Outcome
---
feature: subject-scoped-bank
slug: 2026092209-subject-scoped-bank
owner: Loc Tran
created: 2026-09-22
status: approved
---

## Success signal
In an org with Toán and Vật lý questions, choosing "Toán" then "Bộ lọc" shows only Toán topics (with
subtree counts) and Toán/shared tags; picking "Hàm số" + "Thi thử" + nguồn "Sở GD&ĐT Ninh Bình" shows
chips for each and the matching count, and the URL reproduces the view.

## Out of scope
- Cross-subject search (a "mọi môn" mode)
- Saved filter presets
- Faceted search for students

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher (bank) | Picks "Môn" among eight dropdowns; topics/tags of all subjects | Picks the subject once (tabs); every filter only shows that subject's topics/tags, with counts |
| Teacher (exam matrix) | Topic/tag pickers list every subject | Only the exam's subject |
| Org admin (tags) | One tag list for all subjects | Tags per subject, plus shared tags (nguồn đề, "Có hình vẽ"…) |

## Constraints
| Kind | Detail |
| --- | --- |
| UI | shadcn components only, URL search params are the state, filtering server-side |
| Data | Existing tags keep working; shared tags stay shared |
