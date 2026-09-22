---
id: UOW-03
slug: header-upload
title: Header metadata suggestions and multi-file upload
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-04]
verifies: [AC-09, AC-10]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Header metadata suggestions and multi-file upload

## Demo script
1. Drop the 18 files at once → 18 rows queued; dropping one again → 'đã có'
2. A parsed document shows Nguồn: Sở GD Ninh Bình, 2024-2025, Toán, Thi thử lần 1, 90 phút
3. Its questions are Toán, lớp 12, Thi thử, tagged with the source

## In scope
- header.py + apply in pipeline
- PATCH /documents/{id}
- UploadForm multi-file
- Detected metadata on the document

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-09, AC-10 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
