---
id: UOW-01
slug: rule-and-trace
title: Quy tắc vị trí và dấu vết mức độ
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-02, AC-04]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Quy tắc vị trí và dấu vết mức độ

## Demo script
1. Câu Phần I số 1 ra nb, Phần III ra vd — thuần, không cần model
2. Người đặt mức độ thì dấu vết là manual; lệnh máy không đổi được nó

## In scope
- difficulty_source column
- position rule
- manual is untouchable

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-02, AC-04 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4

## Verification evidence
Không áp dụng: ba UoW này không đổi một màn hình nào — chúng là một cột, một quy tắc thuần, một lượt model trong
worker, một script đo và một lệnh điền. Chúng được kiểm ở nơi kiểm được: `tests/unit/test_ingestion_rules.py`
cho quy tắc và cách đọc trả lời của model, `tests/test_ingest_pipeline.py` cho độ phủ sau khi tách và cho đường
xuống thang khi model hỏng, `tests/test_golden_official.py` cho việc bộ 18 đề chuẩn không đổi, và
`tests/test_bank_api.py` cho `manual` là bất khả xâm phạm. Không viết `07-verification.md`, nên không có ô bằng
chứng nào được đánh dấu ở đây.
