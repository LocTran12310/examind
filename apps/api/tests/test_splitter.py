from app.modules.ingestion.domain.services.lines import Line
from app.modules.ingestion.domain.services.splitter import split


def L(text: str) -> list[Line]:
    return [Line(t) for t in text.strip("\n").split("\n")]


def by_num(res):
    return {q.number: q for q in res.questions}


def test_mcq_options_on_separate_lines_with_inline_answer_and_solution():
    res = split(L("""
Câu 1. Cho hàm số $y = x^2 - 4x + 3$. Tọa độ đỉnh là
A. $(2; -1)$
B. $(-2; 15)$
C. $(4; 3)$
D. $(1; 0)$
Lời giải
Ta có $x_I = 2$, $y_I = -1$.
Chọn A.
Câu 2: Tập nghiệm của $x^2 = 1$ là
A. $\\{1\\}$   B. $\\{-1\\}$   C. $\\{-1; 1\\}$   D. $\\emptyset$
Đáp án: C
"""))
    q1, q2 = by_num(res)[1], by_num(res)[2]
    assert q1.type == "mcq" and [o["label"] for o in q1.options] == list("ABCD")
    assert q1.options[0]["content"] == "$(2; -1)$"
    assert q1.answer == {"key": "A"} and q1.answer_source == "inline"
    assert "x_I = 2" in q1.solution and q1.confidence >= 0.85, q1.issues
    assert [o["content"] for o in q2.options] == ["$\\{1\\}$", "$\\{-1\\}$", "$\\{-1; 1\\}$", "$\\emptyset$"]
    assert q2.answer == {"key": "C"}
    assert "thiếu lời giải" in q2.issues and q2.confidence >= 0.85


def test_two_per_line_options_and_emphasised_answer():
    res = split(L("""
**Câu 3.** Giá trị của $\\log_2 8$ bằng
A. 2 B. 4
**[C.]{.underline}** 3 D. 8
"""))
    q = by_num(res)[3]
    assert [o["content"] for o in q.options] == ["2", "4", "3", "8"]
    assert q.answer == {"key": "C"} and q.answer_source == "format"


def test_option_with_image_continuation_line():
    res = split(L("""
Câu 5. Đồ thị nào là đồ thị hàm số $y=x^2$?
A. Đường thẳng
B. Hyperbol
C. Parabol
![](asset:11111111-1111-1111-1111-111111111111)
D. Đường tròn
"""))
    q = by_num(res)[5]
    assert "asset:11111111" in q.options[2]["content"] and q.options[3]["content"] == "Đường tròn"


def test_answer_key_list_and_table():
    body = "\n".join(f"Câu {i}. Đề {i}\nA. a\nB. b\nC. c\nD. d" for i in range(1, 7))
    res = split(L(body + """
BẢNG ĐÁP ÁN
1.A 2.C 3.B
Câu | 4 | 5 | 6
Đáp án | D | A | B
"""))
    got = {q.number: q.answer["key"] for q in res.questions}
    assert got == {1: "A", 2: "C", 3: "B", 4: "D", 5: "A", 6: "B"}
    assert all(q.answer_source == "key" for q in res.questions)


def test_trailing_solutions_section_attaches_without_duplicates():
    body = "\n".join(f"Câu {i}. Đề {i}\nA. a\nB. b\nC. c\nD. d" for i in range(1, 4))
    res = split(L(body + """
HƯỚNG DẪN GIẢI
Câu 1. Ta có ... Chọn B.
Câu 2.
Lời giải
Biến đổi ... Vậy chọn D.
Câu 3. Đáp án: A
Giải thích ngắn.
"""))
    assert len(res.questions) == 3
    q = by_num(res)
    assert q[1].answer == {"key": "B"} and "Ta có" in q[1].solution
    assert q[2].answer == {"key": "D"} and "Biến đổi" in q[2].solution
    assert q[3].answer == {"key": "A"} and q[3].solution == "Giải thích ngắn."


def test_implicit_restart_is_treated_as_solutions():
    res = split(L("""
Câu 1. Đề 1
A. a
B. b
C. c
D. d
Câu 2. Đề 2
A. a
B. b
C. c
D. d
Câu 1. Chọn C vì ...
Câu 2. Chọn A.
"""))
    assert len(res.questions) == 2
    assert by_num(res)[1].answer == {"key": "C"} and by_num(res)[2].answer == {"key": "A"}


def test_thpt_2025_parts():
    res = split(L("""
PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.
Câu 1. Đề trắc nghiệm
A. 1
B. 2
C. 3
D. 4
PHẦN II. Câu trắc nghiệm đúng sai.
Câu 1. Cho hàm số $f(x) = x^3 - 3x$.
a) $f'(x) = 3x^2 - 3$.
b) Hàm số đồng biến trên $\\mathbb{R}$.
c) $f(1) = -2$.
d) Hàm số có hai điểm cực trị.
PHẦN III. Câu trắc nghiệm trả lời ngắn.
Câu 1. Tính $\\int_0^1 2x\\,dx$.
Đáp án: 1
BẢNG ĐÁP ÁN
PHẦN I
1.C
PHẦN II
Câu 1: a) Đ b) S c) Đ d) Đ
"""))
    qs = {(q.part, q.number): q for q in res.questions}
    mcq, tf, short = qs[("1", 1)], qs[("2", 1)], qs[("3", 1)]
    assert mcq.type == "mcq" and mcq.answer == {"key": "C"}
    assert tf.type == "true_false" and [o["label"] for o in tf.options] == list("abcd")
    assert tf.answer == {"a": True, "b": False, "c": True, "d": True}
    assert [o["is_true"] for o in tf.options] == [True, False, True, True]
    assert short.type == "short_answer" and short.answer == {"value": "1"}
    assert all(q.confidence >= 0.85 for q in res.questions), [(q.number, q.issues) for q in res.questions]


def test_tf_verdicts_from_solution():
    res = split(L("""
PHẦN II. Đúng sai
Câu 2. Cho dãy số.
a) S1
b) S2
c) S3
d) S4
Lời giải
a) Đúng. b) Sai. c) Sai. d) Đúng.
"""))
    q = res.questions[0]
    assert q.answer == {"a": True, "b": False, "c": False, "d": True}


def test_low_confidence_and_issues():
    res = split(L("""
Câu 7. Đề thiếu phương án
A. 1
B. 2
C. 3
Câu 8. Không có đáp án
A. 1
B. 2
C. 3
D. 4
"""))
    q7, q8 = by_num(res)[7], by_num(res)[8]
    assert q7.confidence < 0.85 and "thiếu phương án" in q7.issues and "thiếu đáp án" in q7.issues
    assert q8.confidence < 0.85 and q8.issues[:1] == ["thiếu đáp án"]


def test_essay_bai_headers_and_ocr_cap():
    lines = L("""
Bài 1. (2,0 điểm) Giải phương trình $x^2 - 5x + 6 = 0$.
Bài 2. Chứng minh rằng tam giác ABC cân.
""")
    for l in lines:
        l.ocr = True
    res = split(lines)
    assert [q.type for q in res.questions] == ["essay", "essay"]
    assert "Giải phương trình" in res.questions[0].stem  # "Giải" inside a stem is not a solution marker
    assert all(q.confidence <= 0.8 and "OCR" in q.issues for q in res.questions)


def test_numbered_fallback_without_cau_headers():
    res = split(L("""
1. Đề một
A. a
B. b
C. c
D. d
2. Đề hai
A. a
B. b
C. c
D. d
"""))
    assert [q.number for q in res.questions] == [1, 2]


def test_answer_conflict_flagged():
    res = split(L("""
Câu 1. Đề
A. a
B. b
C. c
D. d
Đáp án: B
BẢNG ĐÁP ÁN
1.C
"""))
    q = res.questions[0]
    assert q.answer == {"key": "B"} and "đáp án không khớp bảng đáp án" in q.issues and q.confidence < 0.85


def test_preamble_kept_and_stem_multiline():
    res = split(L("""
SỞ GD&ĐT HÀ NỘI
ĐỀ KIỂM TRA GIỮA KỲ I
Câu 1. Cho hình vẽ:
![](asset:22222222-2222-2222-2222-222222222222)
Diện tích tam giác là
A. 1
B. 2
C. 3
D. 4
Đáp án: D
"""))
    assert res.preamble[:2] == ["SỞ GD&ĐT HÀ NỘI", "ĐỀ KIỂM TRA GIỮA KỲ I"]
    q = res.questions[0]
    assert q.stem.startswith("Cho hình vẽ:") and "asset:2222" in q.stem and q.stem.endswith("Diện tích tam giác là")


def test_essay_inside_mcq_exam_is_flagged():
    res = split(L("""
Câu 1. Đề
A. a
B. b
C. c
D. d
Đáp án: A
Câu 2. Giá trị của $2^2$? Các lựa chọn: 3; 4; 5; 8.
"""))
    q2 = by_num(res)[2]
    assert q2.type == "essay" and "không nhận ra phương án" in q2.issues and q2.confidence < 0.85


def test_ocr_options_without_space_after_label():
    res = split(L("""
Câu 6. Tam giác ABC có AB = 3, AC = 11. Diện tích bằng
A. 33
B. 17.5
C. 16.5
D.14
"""))
    q = res.questions[0]
    assert [o["content"] for o in q.options] == ["33", "17.5", "16.5", "14"]


def test_ocr_glued_symbol_options_and_no_false_split_inside_words():
    res = split(L("""
Câu 2. Tập A ∩ B là
A. 1
B. 1; 2; 7; 12
C.Ø
D.2;7
Câu 3. Cho vectơ AB.AC = 0 và hai điểm M, N. Chọn đáp án đúng
A. 1
B. 2
C. 3
D. 4
"""))
    q2, q3 = res.questions
    assert [o["content"] for o in q2.options] == ["1", "1; 2; 7; 12", "Ø", "2;7"]
    assert "AB.AC" in q3.stem and len(q3.options) == 4
