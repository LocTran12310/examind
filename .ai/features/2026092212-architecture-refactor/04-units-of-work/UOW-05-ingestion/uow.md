---
id: UOW-05
slug: ingestion
title: Documents and ingestion
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02, US-03]
verifies: [AC-01, AC-02, AC-04, AC-05, AC-06]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-05 — Documents and ingestion

## Demo script
1. Tải lại 18 đề: báo trùng
2. Golden 18 đề giữ nguyên số liệu
3. Tạo đề từ tài liệu

## In scope
- documents
- assets
- pipeline domain services + adapters
- ai models
- ingestion settings
- worker

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-04, AC-05, AC-06 pass
- [x] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
