---
id: UOW-01
slug: foundation-tags
title: Layered foundation and the Tags slice (API + web)
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02, US-04]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05, AC-08]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Layered foundation and the Tags slice (API + web)

## Demo script
1. POST /api/tags/search with {filters:{name:{operator:'+',value:'ph'}}} → {data,total,page,limit}
2. Trang Tags: lọc, sắp xếp, phân trang, tạo/sửa/xoá; bảng tự làm mới (không reloadKey)
3. lint-imports: every contract kept

## In scope
- shared kernel
- import-linter
- error body + request id
- taxonomy/tags module
- web skeleton: query client, http, search body, keys, eslint boundaries
- Tags page

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03, AC-04, AC-05, AC-08 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
