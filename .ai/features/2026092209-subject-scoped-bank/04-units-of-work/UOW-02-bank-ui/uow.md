---
id: UOW-02
slug: bank-ui
title: Subject tabs, Bộ lọc sheet with counts, chips; exam matrix and Tags page by subject
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-01, US-02, US-03, US-04]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-08]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Subject tabs, Bộ lọc sheet with counts, chips; exam matrix and Tags page by subject

## Demo script
1. Bank: Toán (396) tab → Bộ lọc → Hàm số + Thi thử + Sở GD&ĐT Ninh Bình → Áp dụng → chips + count; reload keeps it
2. Switch to Vật lý → topic/tag chips gone, others stay
3. Exam of Toán → matrix topic picker shows only Toán topics

## In scope
- SubjectTabs, FilterSheet, FilterChips, BankFilters
- Bank page
- Exam page topics/tags
- Tags page subject

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-08 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
