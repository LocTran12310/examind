---
feature: review-ux
slug: 2026092303-review-ux
owner: Loc Tran
created: 2026-09-23
status: approved
---

# Intent — Make reviewing a parsed paper readable and reversible

## Problem
Loc Tran, walking the flow upload → tách câu → duyệt (chat, 2026-09-23, with screenshots):
- The "Tình trạng" column carries up to six badges per document and cannot be filtered, so the list is noise.
- "Kiểm tra ngẫu nhiên" means nothing to a teacher: it is the 5% sample of auto-approved questions the system
  draws to catch itself being wrong, and nothing on screen says so.
- Whether a document still needs work is hard to read at a glance.
- The review page shows only what is pending. Once a question is approved it disappears: it cannot be re-read,
  corrected or un-approved from there. A mistake made in a keystroke ("Duyệt (Enter)") has no way back.
- The points of an exam exist (0,25 · 1,0 · 0,5 per type, editable per question, scaled to 10) but nothing on
  screen shows where they are set, so it reads as if a paper cannot be weighted.

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher reviewing a paper | Six badges, no filter, no way back to an approved question | One state per document plus a filter; every question reachable, editable and reversible |
| Teacher weighting a paper | Cannot find where points live | The exam screen states the per-section points and the total, and says when it is not 10 |
| Owner | Cannot tell which papers are finished | "Còn N cần xem" per document, filterable, sortable |

## Success signal
A teacher opens Duyệt câu hỏi, filters to the papers that still need work, opens one, reads any question whatever
its state, corrects an answer key that was approved by mistake, and sees the change take effect — without leaving
the page or asking anyone what a badge means.

## Out of scope
- Changing what the triage decides (auto-approve thresholds, duplicate detection, the 5% sample size)
- Changing how points are computed (ADR from exam-practice stands: per-type defaults, per-question override, scale to 10)
- A new reviewer-assignment workflow

## Constraints
| Kind | Detail |
| --- | --- |
| Data | No schema change; states already exist on `questions.status` and `spot_check` |
| Contract | Lists stay on the search contract; filters are ordinary columns |
| UI | shadcn components, Vietnamese copy, the keyboard flow of the queue stays |
