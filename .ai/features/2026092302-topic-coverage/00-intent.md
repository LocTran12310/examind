---
feature: topic-coverage
slug: 2026092302-topic-coverage
owner: Loc Tran
created: 2026-09-23
status: approved
---

# Intent — Every question belongs to a topic, or someone is asked about it

## Problem
102 of 377 questions in the live bank have no topic: 101 of them are `auto_approved`, so nobody is ever asked
about them. A question without a topic is invisible to mastery, to the practice planner and to every report by
topic — roughly a quarter of the answers a student gives cannot move their growth path. They come from all 18
official papers, 5–10 per paper, and they are ordinary maths questions: the suggestion step simply did not reach
its confidence threshold and the pipeline stayed silent about it. F14 made the number visible; this feature
clears the backlog and stops it refilling.

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher | No way to find untagged questions, no suggestions, one-by-one editing | A queue of untagged questions with suggested topics, keyboard-fast, bulk apply |
| Student | Answers on untagged questions never move mastery | Their work counts, because the bank is tagged |
| Owner | New uploads quietly add untagged approved questions | An untagged question waits for review instead of being auto-approved |

## Success signal
The live bank reaches 0 untagged questions in the ingested set, a teacher can clear ~20 questions in a few
minutes, and a re-upload of an official paper whose questions cannot be classified leaves them in the review
queue with their suggestions instead of auto-approving them.

## Out of scope
- Changing the ingestion classifier itself (keyword cues, kNN, tagging model) beyond reusing it on demand
- Multi-topic tagging (a question keeps one primary topic plus optional extra topics as today)
- Bloom/competency levels

## Constraints
| Kind | Detail |
| --- | --- |
| Reuse | Suggestions reuse the existing topic rules; no second classifier |
| Layers | The rules live in ingestion; the bank reaches them through an application API, never directly |
| Data | No destructive change; assigning a topic is the existing bulk command |
