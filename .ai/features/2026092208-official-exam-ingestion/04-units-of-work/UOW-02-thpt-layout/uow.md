---
id: UOW-02
slug: thpt-layout
title: THPT 2025 layout: per-part answer tables, verdicts, header-less solutions; golden set of 18
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-03]
verifies: [AC-04, AC-05, AC-06, AC-07, AC-08]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — THPT 2025 layout: per-part answer tables, verdicts, header-less solutions; golden set of 18

## Demo script
1. Import d01 → Phần III Câu 1 answer 3 from the per-part table, solution attached
2. Import Lương Tài 2 (no HƯỚNG DẪN GIẢI title) → 22 questions, not 44
3. golden_live.py over the 18 files prints 396/396, answers ≥ 98 %

## In scope
- Splitter rules + table tests
- Golden expectations + live runner

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-04, AC-05, AC-06, AC-07, AC-08 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
