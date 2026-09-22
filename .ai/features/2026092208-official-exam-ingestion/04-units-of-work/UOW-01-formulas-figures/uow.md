---
id: UOW-01
slug: formulas-figures
title: MathType formulas become LaTeX, WMF/EMF figures become PNG
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — MathType formulas become LaTeX, WMF/EMF figures become PNG

## Demo script
1. Upload the Nguyễn Khuyến .docx → review queue shows Câu 1 with KaTeX $\left(u_{n}\right)$, $u_{1}=-1$
2. Câu 4 shows the cube figure as PNG; Phần II Câu 1 graph as PNG
3. Document log lists 475 equations, 0 failed

## In scope
- mtef.py reader + LaTeX
- docx token swap
- vector_images.py + Dockerfile
- document_store conversion

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
