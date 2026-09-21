---
id: UOW-03
slug: ai-model-choice
title: Admins register AI models; teachers choose them per upload
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-04, US-05]
verifies: [AC-13, AC-14, AC-15, AC-16, AC-17, AC-18, AC-19, AC-20]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Admins register AI models; teachers choose them per upload

## Demo script
1. As org_admin open /org/ai-models → 'Phát hiện model Ollama' lists pulled models; add one; 'Kiểm tra' → ok
2. Add an OpenAI-compatible model with an API key → list shows 'Có khóa', key never shown
3. As super_admin add a system model → org admin sees it as 'Hệ thống', cannot edit
4. Open /org/settings/ingestion, set default mode 'Quy tắc + AI' and the model
5. Upload samples/exams/de-kho.docx with 'Cấu hình xử lý' → rule+AI → low-confidence questions show parse_method AI and the model name
6. Stop the model server, re-parse → questions keep rule results with issue 'AI không phản hồi'

## In scope
- ai_models registry + encryption + permissions
- Ollama/OpenAI-compatible/Anthropic adapters, discover, test
- AI fallback with model chain, vision OCR engine, re-parse
- Org ingestion defaults
- AI models UI, upload config, re-parse UI

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| No local model on the dev machine | Adapters tested against a stub HTTP server; smoke test with a small Ollama model |

## Definition of done
- [ ] All of AC-13, AC-14, AC-15, AC-16, AC-17, AC-18, AC-19, AC-20 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
