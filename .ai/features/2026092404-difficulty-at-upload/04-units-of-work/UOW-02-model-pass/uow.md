---
id: UOW-02
slug: model-pass
title: Lượt model trong pipeline tách đề
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02, AC-03]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Lượt model trong pipeline tách đề

## Demo script
1. Tải một đề lên: tách xong mọi câu đều có mức độ
2. Tắt model: đề vẫn tách xong, mọi câu vẫn có mức độ, nhật ký có cảnh báo

## In scope
- difficulty prompt
- pipeline stage
- graceful degradation

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4

## Verification evidence
Không áp dụng: ba UoW này không đổi một màn hình nào — chúng là một cột, một quy tắc thuần, một lượt model trong
worker, một script đo và một lệnh điền. Chúng được kiểm ở nơi kiểm được: `tests/unit/test_ingestion_rules.py`
cho quy tắc và cách đọc trả lời của model, `tests/test_ingest_pipeline.py` cho độ phủ sau khi tách và cho đường
xuống thang khi model hỏng, `tests/test_golden_official.py` cho việc bộ 18 đề chuẩn không đổi, và
`tests/test_bank_api.py` cho `manual` là bất khả xâm phạm. Không viết `07-verification.md`, nên không có ô bằng
chứng nào được đánh dấu ở đây.
