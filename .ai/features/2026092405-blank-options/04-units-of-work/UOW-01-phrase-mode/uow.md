---
id: UOW-01
slug: phrase-mode
title: Phương án được đọc như một cụm, không như một tài liệu
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02, AC-03]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Phương án được đọc như một cụm, không như một tài liệu

## Demo script
1. Câu có phương án 108. / 31. / 13. / 36. hiện đủ bốn số ở màn duyệt và màn làm bài
2. Phương án có công thức, chữ, hình không đổi
3. Đề bài có danh sách đánh số vẫn là danh sách

## In scope
- phrase mode in Markdown
- options use it

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
- [ ] `make verify f=.ai/features/2026092405-blank-options` green on local, the only required environment
- [ ] Evidence exists for every AC in `verifies`, at both viewports
- [ ] `08-evidence.md` regenerated and its commit sha matches HEAD
- [ ] Every screenshot read: each one shows the claim its step makes, on the page the step names
