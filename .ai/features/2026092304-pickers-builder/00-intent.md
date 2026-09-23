---
feature: pickers-builder
slug: 2026092304-pickers-builder
owner: Loc Tran
created: 2026-09-23
status: approved
---

# Intent — Pickers that tell the truth, and a builder that lets the teacher decide

## Problem
Loc Tran, walking tagging and exam building (chat, 2026-09-23, with screenshots):
- Pressing `T` on a question, or "Chuyên đề khác…" in the tagging queue, opens an empty picker even though a
  suggestion is on screen — the teacher retypes what the system already guessed.
- The document filter of the tagging queue prints all 18 papers at once; it needs to scroll and to load as it goes.
- The queue can select many questions but only apply **one** topic to all of them; there is no "take each row's
  own suggestion", which is the whole point of having suggestions per question.
- The bank's "Chưa phân môn" tab lists 21 questions and offers no way to give them a subject or a grade: selecting
  them leads nowhere.
- The topic picker shows a number that a teacher reads as "questions" and is in fact the count of **child topics**.
  A blueprint row can therefore be built on a topic with no questions at all, and nothing says so.
- The blueprint row wraps onto two lines and reads badly.
- "Đổi câu" replaces a question with one the system picks; there is no way to choose from the bank.

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher tagging | Picker opens blank; one topic for a whole selection | Picker opens on the suggestion; a selection can take each row's own suggestion in one click |
| Teacher curating the bank | "Chưa phân môn" is a dead end | Subject and grade can be set for the selected questions |
| Teacher building an exam | Numbers mean child topics; empty topics accepted silently; swaps are automatic | Numbers mean questions; an empty topic says so; a swap can be chosen from the bank |

## Success signal
A teacher clears a page of the tagging queue with one click on the suggestions, gives the 21 unclassified
questions a subject, and builds a 15-question blueprint without ever choosing a topic that has no questions.

## Out of scope
- Changing how suggestions are produced (topic-coverage owns that)
- Changing the scoring or the points model
- A new bank search UI beyond the filters that already exist

## Constraints
| Kind | Detail |
| --- | --- |
| Contract | Lists and counts stay on the search/facets contract |
| UI | shadcn only; the keyboard flow of the review queue stays |
| Data | No schema change |
