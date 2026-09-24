---
id: UOW-03
slug: measure-backfill
title: Đo trước khi tin, rồi điền cho câu cũ
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-02, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Đo trước khi tin, rồi điền cho câu cũ

## Demo script
1. Báo cáo: độ phủ của model, đồng thuận với quy tắc vị trí, phân bố hai bên
2. Lệnh điền: chỉ chạm câu rỗng, chạy lại không đổi gì thêm

## In scope
- difficulty_report.py
- backfill command

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-02, AC-05 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4

## Verification evidence
Không áp dụng: ba UoW này không đổi một màn hình nào — chúng là một cột, một quy tắc thuần, một lượt model trong
worker, một script đo và một lệnh điền. Chúng được kiểm ở nơi kiểm được: `tests/unit/test_ingestion_rules.py`
cho quy tắc và cách đọc trả lời của model, `tests/test_ingest_pipeline.py` cho độ phủ sau khi tách và cho đường
xuống thang khi model hỏng, `tests/test_golden_official.py` cho việc bộ 18 đề chuẩn không đổi, và
`tests/test_bank_api.py` cho `manual` là bất khả xâm phạm. Không viết `07-verification.md`, nên không có ô bằng
chứng nào được đánh dấu ở đây.
