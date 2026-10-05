# School years, student history 10 → 12, org ↔ user assignment

## Problem
Classes only carry a year string. When a student moves from 10A1 to 11A1 nothing links the two
years, reports count old answers under the student's *current* class, and there is no way to
roll a center over to the next year. Documents are tagged "Giữa kỳ" and "hk1" separately, while
teachers think in "Giữa kỳ 1 / Cuối kỳ 2". Org memberships can only be managed from inside an
org, one direction at a time, and nothing shows what was changed.

## Outcome
---
feature: school-years
slug: 2026092207-school-years
owner: Loc Tran
created: 2026-09-22
status: approved
---

## Success signal
After "Chuyển năm học" 2026-2027 → 2027-2028, a student of 10A1 is in 11A1, her lớp-10 answers
still report under 10A1 / 2026-2027, her record shows both years, and every change to a closed
year appears in its history.

## Out of scope
- Custom terms (only HK1/HK2 — Loc Tran)
- Timetables, attendance, fees
- Report cards / official transcripts

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Org admin | Types "2026-2027" per class | Picks the year in the header; classes, structure, reports follow it |
| Org admin at year end | Recreates every class by hand | Runs "Chuyển năm học": 10A1 → 11A1, 12 → tốt nghiệp, exceptions per student |
| Teacher | Class report mixes a student's past years | Report per year / term; each answer remembers year and classes |
| Teacher / parent meeting | No history | "Hồ sơ học sinh": classes and results per year across 10 → 12 |
| Uploader | Two fields for "Giữa kỳ" and "HK1" | One "Đợt kiểm tra": Giữa kỳ 1, Cuối kỳ 1, Giữa kỳ 2, Cuối kỳ 2, … |
| Super admin | Manages members only inside one org | Assigns users to orgs from the org screen **and** orgs to a user from the user screen |

## Constraints
| Kind | Detail |
| --- | --- |
| Data | Existing classes and answers are backfilled into years; nothing is lost |
| Closed years | Still editable (Loc Tran), every change audited and visible |
| UI | shadcn components, server-side DataTable, URL state |
