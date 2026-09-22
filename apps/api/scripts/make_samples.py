"""Generate the sample exam files used by golden tests and demos.

Run inside the api image (needs pandoc):
    docker compose --profile test run --rm -v "$PWD/samples:/out" api-test python scripts/make_samples.py /out/exams

Writes, next to each file, a `<name>.expected.json` with the ground truth the golden test compares to.
"""
import json
import math
import os
import random
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.shared.infrastructure.png import Canvas  # noqa: E402

LABELS = "ABCD"


def parabola_png() -> bytes:
    c = Canvas(240, 180)
    ox, oy, s = 60, 120, 30
    c.line(0, oy, 239, oy, (150, 150, 150))
    c.line(ox, 0, ox, 179, (150, 150, 150))
    for i in range(1601):
        x = -1 + i * 6 / 1600
        c.dot(ox + x * s, oy - (x * x - 4 * x + 3) * s, (37, 83, 230), 1)
    return c.encode()


def triangle_png() -> bytes:
    c = Canvas(220, 160)
    a, b, cc = (30, 140), (190, 140), (80, 30)
    for p, q in ((a, b), (b, cc), (cc, a)):
        c.line(*p, *q, (40, 40, 40), 1)
    for ang in range(60):
        t = math.radians(ang)
        c.dot(a[0] + 18 * math.cos(t), a[1] - 18 * math.sin(t), (220, 40, 40))
    return c.encode()


def vector_png() -> bytes:
    c = Canvas(200, 140)
    c.line(20, 120, 180, 40, (37, 83, 230), 1)
    c.line(180, 40, 165, 40, (37, 83, 230), 1)
    c.line(180, 40, 172, 53, (37, 83, 230), 1)
    return c.encode()


# (topic keyword, stem, correct, distractors, solution) — deterministic Toán 10 items.
def mcq_bank(rng: random.Random) -> list[dict]:
    items = []
    for i in range(40):
        kind = i % 8
        a = rng.randint(1, 5)
        b = rng.randint(1, 9)
        if kind == 0:
            p, q = rng.randint(1, 4), rng.randint(5, 9)
            stem = f"Tọa độ đỉnh của parabol $y = x^2 - {2 * p}x + {p * p - q}$ là"
            correct = f"$({p};\\,{-q})$"
            wrong = [f"$({-p};\\,{q})$", f"$({p};\\,{q})$", f"$({2 * p};\\,{-q})$"]
            sol = f"Hoành độ đỉnh $x_I = -\\dfrac{{b}}{{2a}} = {p}$, tung độ $y_I = {-q}$."
            topic = "Hàm số bậc hai và đồ thị"
        elif kind == 1:
            stem = f"Cho tập hợp $A = \\{{1; 2; {a + 2}\\}}$ và $B = \\{{2; {a + 2}; {a + 7}\\}}$. Tập $A \\cap B$ là"
            correct = f"$\\{{2; {a + 2}\\}}$"
            wrong = ["$\\{1\\}$", f"$\\{{1; 2; {a + 2}; {a + 7}\\}}$", "$\\varnothing$"]
            sol = "Giao của hai tập hợp gồm các phần tử thuộc cả hai tập."
            topic = "Mệnh đề và tập hợp"
        elif kind == 2:
            stem = f"Mệnh đề phủ định của mệnh đề \"$\\forall x \\in \\mathbb{{R}},\\ x^2 + {b} > 0$\" là"
            correct = f"\"$\\exists x \\in \\mathbb{{R}},\\ x^2 + {b} \\le 0$\""
            wrong = [f"\"$\\forall x \\in \\mathbb{{R}},\\ x^2 + {b} \\le 0$\"", f"\"$\\exists x \\in \\mathbb{{R}},\\ x^2 + {b} < 0$\"",
                     f"\"$\\forall x \\in \\mathbb{{R}},\\ x^2 + {b} < 0$\""]
            sol = "Phủ định của $\\forall$ là $\\exists$, phủ định của $>$ là $\\le$."
            topic = "Mệnh đề"
        elif kind == 3:
            x1, x2 = a, a + b
            stem = f"Tam thức bậc hai $f(x) = x^2 - {x1 + x2}x + {x1 * x2}$ âm khi và chỉ khi"
            correct = f"${x1} < x < {x2}$"
            wrong = [f"$x < {x1}$ hoặc $x > {x2}$", f"$x < {x1}$", f"$x > {x2}$"]
            sol = f"$f(x)$ có hai nghiệm ${x1}$ và ${x2}$, hệ số $a = 1 > 0$ nên $f(x) < 0$ trong khoảng hai nghiệm."
            topic = "Dấu của tam thức bậc hai"
        elif kind == 4:
            stem = f"Cho $\\vec{{u}} = ({a};\\,{b})$ và $\\vec{{v}} = ({b};\\,{-a})$. Tích vô hướng $\\vec{{u}} \\cdot \\vec{{v}}$ bằng"
            correct = "$0$"
            wrong = [f"${2 * a * b}$", f"${a * a + b * b}$", f"${a * b}$"]
            sol = f"$\\vec{{u}} \\cdot \\vec{{v}} = {a}\\cdot{b} + {b}\\cdot({-a}) = 0$."
            topic = "Tích vô hướng của hai vectơ"
        elif kind == 5:
            ab, ac = a + 2, b + 3
            stem = f"Tam giác $ABC$ có $AB = {ab}$, $AC = {ac}$, $\\widehat{{A}} = 90^\\circ$. Diện tích tam giác $ABC$ bằng"
            area = ab * ac / 2
            correct = f"${area:g}$"
            wrong = [f"${ab * ac:g}$", f"${area + 1:g}$", f"${ab + ac:g}$"]
            sol = f"$S = \\dfrac{{1}}{{2}} AB \\cdot AC = {area:g}$."
            topic = "Hệ thức lượng trong tam giác"
        elif kind == 6:
            stem = f"Số cách chọn {a} học sinh từ một nhóm gồm {a + b} học sinh là"
            correct = f"$C_{{{a + b}}}^{{{a}}}$"
            wrong = [f"$A_{{{a + b}}}^{{{a}}}$", f"${a + b}!$", f"${a}!$"]
            sol = "Mỗi cách chọn là một tổ hợp."
            topic = "Hoán vị, chỉnh hợp, tổ hợp"
        else:
            stem = f"Phương trình đường thẳng đi qua $M({a};\\,{b})$ và có vectơ pháp tuyến $\\vec{{n}} = (1;\\,1)$ là"
            correct = f"$x + y - {a + b} = 0$"
            wrong = [f"$x - y - {a - b} = 0$", f"$x + y + {a + b} = 0$", f"${a}x + {b}y = 0$"]
            sol = f"$1(x - {a}) + 1(y - {b}) = 0 \\iff x + y - {a + b} = 0$."
            topic = "Phương trình đường thẳng"
        pos = rng.randrange(4)
        opts = wrong[:]
        opts.insert(pos, correct)
        items.append({"stem": stem, "options": opts, "answer": LABELS[pos], "solution": sol, "topic": topic})
    return items


def build_mau_toan10(out_dir: str, media: dict) -> tuple[str, dict]:
    rng = random.Random(2026)
    qs = mcq_bank(rng)
    # figures: an image as option C of Câu 5, and one in the solution of Câu 12
    qs[4]["options"][2] = f"Hình dưới đây\n\n![]({media['parabola']}){{width=4cm}}"
    qs[11]["solution"] += f"\n\nHình minh họa:\n\n![]({media['triangle']}){{width=4cm}}"
    qs[7]["stem"] += f"\n\n![]({media['vector']}){{width=3.5cm}}"
    md = ["SỞ GIÁO DỤC VÀ ĐÀO TẠO", "", "**ĐỀ KIỂM TRA GIỮA HỌC KỲ I – TOÁN 10**", "", "*Thời gian làm bài: 90 phút*", ""]
    for i, q in enumerate(qs, 1):
        md.append(f"**Câu {i}.** {q['stem']}")
        md.append("")
        if i % 5 == 0:  # options two per line, separated by tabs
            md.append(f"A. {q['options'][0]}\tB. {q['options'][1]}")
            md.append("")
            md.append(f"C. {q['options'][2]}\tD. {q['options'][3]}")
            md.append("")
        else:
            for label, o in zip(LABELS, q["options"]):
                md.append(f"{label}. {o}")
                md.append("")
        if i <= 20:  # inline solutions for the first half
            md.append("**Lời giải**")
            md.append("")
            md.append(q["solution"])
            md.append("")
            md.append(f"Chọn {q['answer']}.")
            md.append("")
    md += ["**BẢNG ĐÁP ÁN**", ""]
    for start in (1, 21):
        nums = list(range(start, start + 20))
        md.append("| Câu | " + " | ".join(map(str, nums)) + " |")
        md.append("|" + "---|" * (len(nums) + 1))
        md.append("| Đáp án | " + " | ".join(qs[n - 1]["answer"] for n in nums) + " |")
        md.append("")
    md += ["**HƯỚNG DẪN GIẢI**", ""]
    for i in range(21, 41):
        md.append(f"**Câu {i}.** {qs[i - 1]['solution']}")
        md.append("")
    expected = {"questions": [
        {"number": i, "part": None, "type": "mcq", "answer": {"key": q["answer"]}, "n_options": 4, "topic": q["topic"],
         "has_solution": True, "has_image": i in (5, 8, 12)}
        for i, q in enumerate(qs, 1)
    ]}
    return "\n".join(md), expected


def build_thpt2025(out_dir: str, media: dict) -> tuple[str, dict]:
    rng = random.Random(7)
    mc = mcq_bank(rng)[:12]
    md = ["**ĐỀ THAM KHẢO KỲ THI TỐT NGHIỆP THPT NĂM 2025 – MÔN TOÁN**", "",
          "**PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.** Thí sinh trả lời từ câu 1 đến câu 12.", ""]
    exp = []
    for i, q in enumerate(mc, 1):
        md += [f"**Câu {i}.** {q['stem']}", ""] + [f"{l}. {o}\n" for l, o in zip(LABELS, q["options"])]
        exp.append({"number": i, "part": "1", "type": "mcq", "answer": {"key": q["answer"]}, "n_options": 4})
    md += ["**PHẦN II. Câu trắc nghiệm đúng sai.** Thí sinh trả lời từ câu 1 đến câu 4.", ""]
    tf_truth = []
    for i in range(1, 5):
        k = i + 1
        md += [f"**Câu {i}.** Cho hàm số $f(x) = x^3 - {3 * k}x$.", "",
               f"a) $f'(x) = 3x^2 - {3 * k}$.", "", "b) Hàm số đồng biến trên $\\mathbb{R}$.", "",
               "c) $f(0) = 0$.", "", "d) Hàm số có hai điểm cực trị.", ""]
        truth = {"a": True, "b": False, "c": True, "d": True}
        tf_truth.append(truth)
        exp.append({"number": i, "part": "2", "type": "true_false", "answer": truth, "n_options": 4})
    md += ["**PHẦN III. Câu trắc nghiệm trả lời ngắn.** Thí sinh trả lời từ câu 1 đến câu 6.", ""]
    for i in range(1, 7):
        md += [f"**Câu {i}.** Tính $\\displaystyle\\int_0^{{{i}}} 2x\\,dx$.", ""]
        exp.append({"number": i, "part": "3", "type": "short_answer", "answer": {"value": str(i * i)}, "n_options": 0})
    md += ["**BẢNG ĐÁP ÁN**", "", "**PHẦN I**", "", " ".join(f"{i}.{q['answer']}" for i, q in enumerate(mc, 1)), "",
           "**PHẦN II**", ""]
    for i, t in enumerate(tf_truth, 1):
        md += [f"Câu {i}: " + " ".join(f"{k}) {'Đ' if v else 'S'}" for k, v in t.items()), ""]
    md += ["**PHẦN III**", "", " ".join(f"Câu {i}: {i * i}" for i in range(1, 7)), ""]
    return "\n".join(md), {"questions": exp}


def build_kho(out_dir: str, media: dict) -> tuple[str, dict]:
    """Messy layout: options without labels on one line, answer only in prose — the rules should flag these."""
    md = ["**ĐỀ LUYỆN TẬP (định dạng lộn xộn)**", ""]
    exp = []
    for i in range(1, 6):
        md += [f"**Câu {i}.** Giá trị của $2^{i}$ bằng bao nhiêu? Các lựa chọn: {2 ** i - 1}; {2 ** i}; {2 ** i + 1}; {2 ** (i + 1)}.", "",
               "Đáp án đúng là giá trị thứ hai.", ""]
        exp.append({"number": i, "part": None, "type": "mcq", "answer": {"key": "B"}, "n_options": 4, "needs_ai": True})
    for i in range(6, 9):
        md += [f"**Câu {i}.** Nghiệm của phương trình $x - {i} = 0$ là", "", f"A. ${i - 1}$", "", f"B. ${i}$", "", f"C. ${i + 1}$", "", f"D. ${-i}$", "",
               "Chọn B.", ""]
        exp.append({"number": i, "part": None, "type": "mcq", "answer": {"key": "B"}, "n_options": 4})
    return "\n".join(md), {"questions": exp}


LATEX_UNICODE = [
    (r"\\dfrac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)"), (r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)"),
    (r"\\vec\{([^{}]*)\}", r"\1⃗"), (r"\\widehat\{([^{}]*)\}", r"∠\1"), (r"\\mathbb\{R\}", "ℝ"),
    (r"C_\{(\d+)\}\^\{(\d+)\}", r"C(\1,\2)"), (r"A_\{(\d+)\}\^\{(\d+)\}", r"A(\1,\2)"),
    (r"\^\\circ", "°"), (r"\^2", "²"), (r"\^3", "³"), (r"\\le\b", "≤"), (r"\\ge\b", "≥"), (r"\\forall", "∀"),
    (r"\\exists", "∃"), (r"\\in\b", "∈"), (r"\\cap", "∩"), (r"\\cup", "∪"), (r"\\varnothing", "∅"), (r"\\emptyset", "∅"),
    (r"\\cdot", "·"), (r"\\iff", "⇔"), (r"\\int_0\^\{(\d+)\}", r"∫₀^\1"), (r"\\displaystyle", ""), (r"\\,", " "), (r"\\ ", " "),
    (r"\\\{", "{"), (r"\\\}", "}"), (r"\\mathrm\{d\}", "d"),
]


def latex_to_text(s: str) -> str:
    import re as _re

    def conv(m):
        t = m.group(1)
        for pat, rep in LATEX_UNICODE:
            t = _re.sub(pat, rep, t)
        return t.replace("{", "").replace("}", "")

    return _re.sub(r"\$([^$]+)\$", conv, s)


def md_to_pdf(markdown: str, path: str, media_dir: str, columns: int = 1) -> None:
    """Render our sample markdown to a text PDF (fpdf2, DejaVu font) — images embedded where they appear."""
    import re as _re

    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(True, margin=15)
    font_dir = "/usr/share/fonts/truetype/dejavu"
    pdf.add_font("DejaVu", "", f"{font_dir}/DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", f"{font_dir}/DejaVuSans-Bold.ttf")
    pdf.add_page()
    pdf.set_font("DejaVu", size=10.5)
    blocks = [b for b in markdown.split("\n")]

    def emit(cols=None):
        rows = []
        for raw in blocks:
            line = raw.rstrip()
            if not line.strip():
                continue
            parts = _re.split(r"(!\[\]\([^)]+\)(?:\{width=[\d.]+cm\})?)", line)
            if len(parts) > 1:  # images inside a line: text before, image, text after
                for part in parts:
                    img = _re.match(r"^!\[\]\(([^)]+)\)(\{width=([\d.]+)cm\})?$", part.strip())
                    if img:
                        w = float(img.group(3) or 4) * 10
                        if cols is None:
                            pdf.image(os.path.join(media_dir, img.group(1)), w=w)
                            pdf.ln(2)
                        else:
                            cols.image(os.path.join(media_dir, img.group(1)), width=w)
                    elif part.strip():
                        text = latex_to_text(part.replace("**", "").replace("\t", "    ").strip())
                        if cols is None:
                            pdf.set_font("DejaVu", "", 10.5)
                            pdf.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
                        else:
                            cols.write(text + "\n")
                continue
            if line.startswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                if all(set(c) <= set("-") for c in cells):
                    continue
                rows.append(cells)
                continue
            if rows:
                _table(rows)
                rows = []
            bold = line.startswith("**") and line.count("**") >= 2
            text = latex_to_text(line.replace("**", "").replace("*", "").replace("\t", "    "))
            if cols is None:
                pdf.set_font("DejaVu", "B" if bold and len(text) < 60 else "", 10.5)
                pdf.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
            else:
                cols.write(text + "\n")
        if rows:
            _table(rows)

    def _table(rows):
        width = (pdf.w - pdf.l_margin - pdf.r_margin) / len(rows[0])
        pdf.set_font("DejaVu", "", 8)
        for r in rows:
            for c in r:
                pdf.cell(width, 6, c, border=1, align="C")
            pdf.ln()
        pdf.set_font("DejaVu", "", 10.5)
        pdf.ln(2)

    if columns == 1:
        emit()
    else:
        with pdf.text_columns(ncols=columns, gutter=8) as cols:
            emit(cols)
    pdf.output(path)


def pdf_to_scans(pdf_path: str, out_png: str, out_pdf: str, pages: int = 2) -> list[int]:
    """Rasterise the first pages (≈200 dpi) as a fake scan; returns the question numbers visible on them."""
    import re as _re

    from fpdf import FPDF
    import pdfplumber
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf_path)  # closed at the end
    images = []
    for i in range(min(pages, len(doc))):
        img = doc[i].render(scale=200 / 72).to_pil().convert("L")
        images.append(img)
    images[0].save(out_png)
    scan = FPDF(format="A4")
    for i, img in enumerate(images):
        tmp = out_png.replace(".png", f".p{i}.png")
        img.save(tmp)
        scan.add_page()
        scan.image(tmp, x=0, y=0, w=210, h=297)
        os.remove(tmp)
    scan.output(out_pdf)
    doc.close()
    nums = []
    with pdfplumber.open(pdf_path) as p:
        for page in p.pages[:pages]:
            nums += [int(n) for n in _re.findall(r"^Câu (\d+)\.", page.extract_text() or "", _re.M)]
    return nums


def build_two_column() -> tuple[str, dict]:
    rng = random.Random(99)
    qs = mcq_bank(rng)[:10]
    md, exp = ["ĐỀ ÔN TẬP HAI CỘT", ""], []
    for i, q in enumerate(qs, 1):
        md += [f"Câu {i}. {q['stem']}"] + [f"{l}. {o}" for l, o in zip(LABELS, q["options"])] + [f"Đáp án: {q['answer']}", ""]
        exp.append({"number": i, "part": None, "type": "mcq", "answer": {"key": q["answer"]}, "n_options": 4})
    return "\n".join(md), {"questions": exp}


def pdf_numbers(pdf_path: str, pages: int) -> list[int]:
    import re as _re

    import pdfplumber

    with pdfplumber.open(pdf_path) as p:
        return [int(n) for page in p.pages[:pages] for n in _re.findall(r"^Câu (\d+)\.", page.extract_text() or "", _re.M)]


def pandoc_docx(markdown: str, path: str, resource_dir: str) -> None:
    subprocess.run(["pandoc", "-f", "markdown+tex_math_dollars+pipe_tables", "-t", "docx", "-o", path,
                    f"--resource-path={resource_dir}"], input=markdown.encode(), check=True)


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        media = {}
        for name, fn in (("parabola", parabola_png), ("triangle", triangle_png), ("vector", vector_png)):
            path = os.path.join(tmp, f"{name}.png")
            with open(path, "wb") as fh:
                fh.write(fn())
            media[name] = f"{name}.png"  # resolved through --resource-path
        for name, builder in (("de-mau-toan10", build_mau_toan10), ("de-thpt2025-toan", build_thpt2025), ("de-kho", build_kho)):
            md, expected = builder(out_dir, media)
            pandoc_docx(md, os.path.join(out_dir, f"{name}.docx"), tmp)
            with open(os.path.join(out_dir, f"{name}.md"), "w", encoding="utf-8") as fh:
                fh.write(md)
            with open(os.path.join(out_dir, f"{name}.expected.json"), "w", encoding="utf-8") as fh:
                json.dump(expected, fh, ensure_ascii=False, indent=1)
            print("wrote", name)
            if name == "de-mau-toan10":
                md_to_pdf(md, os.path.join(out_dir, f"{name}.pdf"), tmp)
                nums = pdf_to_scans(os.path.join(out_dir, f"{name}.pdf"), os.path.join(out_dir, "de-scan.png"), os.path.join(out_dir, "de-scan.pdf"))
                with open(os.path.join(out_dir, "de-scan.expected.json"), "w", encoding="utf-8") as fh:
                    json.dump({"numbers": nums, "png_numbers": pdf_numbers(os.path.join(out_dir, f"{name}.pdf"), 1)}, fh)
                print("wrote pdf + scans", nums)
        two_col = build_two_column()
        md_to_pdf(two_col[0], os.path.join(out_dir, "de-2cot.pdf"), tmp, columns=2)
        with open(os.path.join(out_dir, "de-2cot.expected.json"), "w", encoding="utf-8") as fh:
            json.dump(two_col[1], fh, ensure_ascii=False, indent=1)
        print("wrote de-2cot")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/out/exams")
