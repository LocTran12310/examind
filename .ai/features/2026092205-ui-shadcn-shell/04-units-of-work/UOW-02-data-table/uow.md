---
id: UOW-02
slug: data-table
title: Server-side DataTable with URL state on users, organisations, classes
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-03, US-04]
verifies: [AC-06, AC-07, AC-08, AC-09, AC-10, AC-11]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Server-side DataTable with URL state on users, organisations, classes

## Demo script
1. Users: type 'bui' in Họ tên filter → URL ?full_name=bui, request carries it, 20/page
2. Open the copied URL in a new tab → same rows, inputs filled
3. Tick 2 users → Xóa asks to confirm; Sửa disabled; Nạp reloads
4. Organisations and Classes use the same table

## In scope
- paging helper + endpoints
- DataTable, filter row, toolbar, pagination, useTableQuery
- Users, orgs, classes screens

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-06, AC-07, AC-08, AC-09, AC-10, AC-11 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
