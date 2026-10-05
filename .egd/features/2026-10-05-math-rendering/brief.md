# Công thức hiển thị dính dòng, lời giải dính chữ

## Problem
Hai lỗi trên cùng một chỗ, `Markdown` (mọi câu hỏi, đáp án, lời giải đều đi qua nó):

- **Dính dòng.** Phân số và số mũ đè lên nét phân số, đè lên dòng trên/dưới: `\frac{1}{\sin^2 x}` có số 1 bị
  gạch ngang, số 2 của `\sin^2` chồng lên chữ `n`. Nguyên nhân: `rehype-katex@7.0.1` render bằng **katex 0.16.47**
  (dependency của nó), còn `layout.tsx` nạp CSS của **katex 0.18.7** (khai trong `package.json` từ commit đầu
  tiên). Bản 0.18 đổi tên class (`.base` → `.katex-base`, `.strut` → `.katex-strut`, `.vbox`, `.hline`, …) nên
  HTML của 0.16 mất chiều cao dòng và vị trí của chỉ số trên/dưới.
- **Dính chữ.** Lời giải nhập về có chữ tiếng Việt nằm **trong** `$…$`, ví dụ
  `$-Ở góc phần tư thứ tư thì : \sin\alpha<0; …$`. Trong math mode KaTeX bỏ dấu cách và in nghiêng từng chữ cái,
  nên học sinh đọc "Ởgócphầntưthứtưthì".

## Outcome
Mọi công thức đã lưu hiển thị đúng hình: phân số, số mũ, căn không chồng lên nhau hay lên dòng khác; chữ tiếng
Việt lọt vào trong công thức đọc như chữ thường — đứng, có dấu cách. Không phải sửa lại dữ liệu đã nhập.

## Success signal
Hai câu trong ảnh chụp của anh (đáp án 3,48 và "Chọn D — góc phần tư thứ tư") hiển thị sạch ở trang làm bài và
trang lời giải, và một test giữ cho CSS và bộ render katex luôn cùng một phiên bản.

## Out of scope
Sửa pipeline nhập (MathType/LaTeX) để chữ không bao giờ lọt vào `$…$` từ đầu — đó là `ingestion-change` với golden
set riêng. Không viết lại dữ liệu đã lưu. Không đổi cách xuống dòng của công thức dài.
