"""THPT 2025 official layout (official-exam-ingestion AC-04..AC-07).

Line streams are cut down from the 18 reference files: an exam part, then "HƯỚNG DẪN GIẢI" that
copies every question with its answer highlighted, answer tables under each PHẦN, verdicts in words.
"""
from app.modules.ingestion.domain.services.lines import Line
from app.modules.ingestion.domain.services.splitter import short_value_of, split


def L(text: str) -> list[Line]:
    return [Line(t) for t in text.strip("\n").split("\n")]


def by_key(res):
    return {(q.part, q.number): q for q in res.questions}


EXAM = """
**PHẦN I: CÂU TRẮC NGHIỆM NHIỀU PHƯƠNG ÁN LỰA CHỌN**
**Câu 1:** Giá trị của $u_{3}$ bằng
**A.** 9. **B.** -16. **C.** 7. **D.** -8.
**Câu 2:** Tiệm cận xiên là
**A.** $y=-x+1$. **B.** $y=x-1$. **C.** $y=-x-1$. **D.** $y=x+1$.
**PHẦN II: CÂU TRẮC NGHIỆM ĐÚNG SAI**
**Câu 1:** Cho hàm số $y=f(x)$.
a) Hàm số nghịch biến trên $(-2;0)$
b) Có tiệm cận xiên $y=x+1$
c) Diện tích bằng 8
d) Có trục đối xứng
**PHẦN III: CÂU TRẮC NGHIỆM TRẢ LỜI NGẮN**
**Câu 1:** Tính chi phí thấp nhất.
**Câu 2:** Tính $D=3a+6b$.
"""


def test_solution_section_merges_answers_tables_and_methods():
    res = split(L(EXAM + """
**HƯỚNG DẪN GIẢI CHI TIẾT**
**PHẦN I: CÂU TRẮC NGHIỆM NHIỀU PHƯƠNG ÁN LỰA CHỌN**
**Câu 1:** Giá trị của $u_{3}$ bằng
[**A.** 9.]{.mark} **B.** -16. **C.** 7. **D.** -8.
**Phương pháp:**
Công thức cấp số cộng
**Cách giải:** Ta có $u_{3}=9$
**Câu 2:** Tiệm cận xiên là
**A.** $y=-x+1$. **B.** $y=x-1$. [**[C]{.underline}.** $y=-x-1$.]{.mark} **D.** $y=x+1$.
**Lời giải**
Tiệm cận xiên qua $(-1;0)$ và $(0;-1)$.
**PHẦN II: CÂU TRẮC NGHIỆM ĐÚNG SAI**
**Câu** | 1
**Đáp án** | SĐSĐ
**Câu 1:** Cho hàm số $y=f(x)$.
a) Hàm số nghịch biến trên $(-2;0)$
b) Có tiệm cận xiên $y=x+1$
c) Diện tích bằng 8
d) Có trục đối xứng
**Cách giải:**
a) Sai: đồng biến.
**PHẦN III: CÂU TRẮC NGHIỆM TRẢ LỜI NGẮN**
**Câu** | 1 | 2
**Đáp án** | 3 | 7,2
**Câu 1:** Tính chi phí thấp nhất.
Vậy chi phí thấp nhất khi $x+2y=3$
**Câu 2:** Tính $D=3a+6b$.
Vậy $D=7,2$
"""))
    qs = by_key(res)
    assert len(res.questions) == 5 and not res.warnings
    q1 = qs[("1", 1)]
    assert q1.answer == {"key": "A"} and q1.answer_source == "format"
    assert q1.solution.startswith("**Phương pháp:**") and "**Cách giải:** Ta có" in q1.solution
    assert "-16" not in q1.solution  # the copied question is not repeated in the solution
    assert qs[("1", 2)].answer == {"key": "C"}
    tf = qs[("2", 1)]
    assert tf.answer == {"a": False, "b": True, "c": False, "d": True} and tf.answer_source == "key"
    assert "Hàm số nghịch biến" not in tf.solution
    assert qs[("3", 1)].answer == {"value": "3"} and qs[("3", 2)].answer == {"value": "7,2"}
    assert qs[("3", 1)].type == "short_answer" and "x+2y=3" in qs[("3", 1)].solution


def test_lower_case_verdicts_and_grid():
    res = split(L("""
**PHẦN II. Câu trắc nghiệm đúng sai.**
**Câu 1:** Cho hàm số.
**a)** Ý một
**b)** Ý hai
**c)** Ý ba
**d)** Ý bốn
Lời giải
Đáp án: a đúng| b sai| c sai| d đúng
**Câu 2:** Cho hình hộp.
**a)** Một
**b)** Hai
**c)** Ba
**d)** Bốn
**Đáp án:**
**a** | **b** | **c** | **d**
**Đ** | **Đ** | **S** | **Đ**
**Giải chi tiết:**
Thể tích là 27.
"""))
    qs = by_key(res)
    assert qs[("2", 1)].answer == {"a": True, "b": False, "c": False, "d": True}
    assert qs[("2", 2)].answer == {"a": True, "b": True, "c": False, "d": True}


def test_solution_pass_without_a_header_and_numbered_parts():
    """Lương Tài 2 repeats PHẦN I after the exam without a title; Quế Võ 1 numbers part I "1."."""
    res = split(L("""
**PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.**
1. Cho hàm số có bảng xét dấu
**A.** Một. **B.** Hai. **C.** Ba. **D.** Bốn.
2. Tốc độ nhỏ nhất của xe là
**A. $3$**. **B. $160$**. **C. $130$**. **D. $70$**.
**PHẦN II. Câu trắc nghiệm đúng sai.**
**Câu 1:** Cho hàm số.
a) Một
b) Hai
c) Ba
d) Bốn
**-------------- HẾT-------------**
**PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.**
**Câu 1.** Cho hàm số có bảng xét dấu
**A.** Một. **B.** Hai. **C.** Ba. **[D.]{.underline}** Bốn.
**Lời giải**
Xét dấu đạo hàm.
**Câu 2.** Tốc độ nhỏ nhất của xe là
**A. $3$**. **B. $160$**. **C. $130$**. **[D.]{.underline} $70$**.
Dựa vào đồ thị.
**PHẦN II. Câu trắc nghiệm đúng sai.**
**Câu 1:** Cho hàm số.
a) Một
b) Hai
c) Ba
d) Bốn
Lời giải
a) Đúng b) Sai c) Đúng d) Sai
"""))
    qs = by_key(res)
    assert sorted(qs) == [("1", 1), ("1", 2), ("2", 1)]
    assert qs[("1", 1)].answer == {"key": "D"} and qs[("1", 1)].solution == "Xét dấu đạo hàm."
    assert qs[("1", 2)].answer == {"key": "D"}  # underline wins over bold on every label
    assert qs[("2", 1)].answer == {"a": True, "b": False, "c": True, "d": False}


def test_numbered_lines_inside_a_cau_part_stay_text():
    res = split(L("""
**Câu 1:** Cho các bước:
1. Tính đạo hàm
2. Lập bảng
**A.** 1. **B.** 2. **C.** 3. **D.** 4.
**Câu 2:** Hai
**A.** 1. **B.** 2. **C.** 3. **D.** 4.
"""))
    assert [q.number for q in res.questions] == [1, 2]
    assert "1. Tính đạo hàm" in res.questions[0].stem


def test_cyrillic_label_and_thpt_default_part_types():
    res = split(L("""
**PHẦN I. Thí sinh trả lời từ câu 1 đến câu 12.**
**Câu 3:** Tiệm cận ngang là
**А.** $y=-3$. **B.** $y=1$. **C.** $y=3$. **D.** $y=-1$.
**PHẦN II. Thí sinh trả lời từ câu 1 đến câu 4.**
**Câu 1:** Cho hàm số.
a) Một
b) Hai
c) Ba
d) Bốn
**PHẦN III. Thí sinh trả lời từ câu 1 đến câu 6**.
**Câu 1:** Tính khoảng cách.
"""))
    qs = by_key(res)
    assert [o["label"] for o in qs[("1", 3)].options] == list("ABCD")
    assert qs[("2", 1)].type == "true_false" and qs[("3", 1)].type == "short_answer"


def test_key_section_then_solutions_and_mismatch_flag():
    """Chuyên ĐHKHTN: a key with 'Mã đề' columns, then the solutions without a heading."""
    res = split(L(EXAM + """
🙢 **HẾT** 🙠
**BẢNG ĐÁP ÁN**
**PHẦN I: Trắc nghiệm nhiều lựa chọn**
**Mã đề** | **1** | **2**
| **A** | **B** |
**PHẦN II: Trắc nghiệm đúng sai**
**Mã đề** | **Câu 1**
| **a)Ð - b)S - c)S - d)Ð** |
**PHẦN III: Trắc nghiệm trả lời ngắn**
**Mã đề** | **Câu 1** | **Câu 2**
| **1,8** | **20** |
**PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.**
**Câu 1.** Giá trị của $u_{3}$ bằng
**A.** 9. **B.** -16. **C.** 7. **D.** -8.
Chọn A
Vì $u_{3}=u_{1}+2d=9$.
**PHẦN III. Câu trắc nghiệm trả lời ngắn.**
**Câu 1.** Tính chi phí thấp nhất.
[**Đáp án:** $4\\text{,}39$.]{.mark}
Ta có …
"""))
    qs = by_key(res)
    assert qs[("1", 1)].answer == {"key": "A"} and qs[("1", 2)].answer == {"key": "B"}
    assert qs[("2", 1)].answer == {"a": True, "b": False, "c": False, "d": True}
    assert qs[("3", 1)].answer == {"value": "4,39"} and "đáp án không khớp bảng đáp án" in qs[("3", 1)].issues
    assert qs[("3", 2)].answer == {"value": "20"} and qs[("3", 2)].answer_source == "key"
    assert qs[("1", 1)].solution == "Vì $u_{3}=u_{1}+2d=9$."  # solutions after the key are not swallowed


def test_short_values():
    assert short_value_of("$45^{\\circ}$.") == "45"
    assert short_value_of("25 (gam/lít).") == "25"
    assert short_value_of("**$4\\text{,}39$**") == "4,39"
    assert short_value_of("−1,5") == "-1,5"
    assert short_value_of("$\\frac{1}{2}$") == "$\\frac{1}{2}$"


def test_word_grid_and_cau_n_key_rows():
    """Sở Ninh Bình: key rows "Câu 1 | Câu 2 …" / values, and a solution grid written in words."""
    res = split(L(EXAM + """
**BẢNG ĐÁP ÁN**
**PHẦN III: Trắc nghiệm trả lời ngắn**
**Câu 1** | **Câu 2**
**1012** | **240**
**HƯỚNG DẪN GIẢI**
**PHẦN II. Trắc nghiệm chọn đúng sai.**
**Câu 1.** Cho hàm số $y=f(x)$.
[a]{.underline}) Hàm số nghịch biến trên $(-2;0)$
b) Có tiệm cận xiên $y=x+1$
c) Diện tích bằng 8
d) Có trục đối xứng
**Lời giải**
a | b | c | d
Đúng | Sai | Đúng | Sai
+ Theo đồ thị …
"""))
    qs = by_key(res)
    assert qs[("2", 1)].answer == {"a": True, "b": False, "c": True, "d": False}
    assert qs[("3", 1)].answer == {"value": "1012"} and qs[("3", 2)].answer == {"value": "240"}
    assert qs[("3", 1)].solution == ""  # the key table did not leak into a solution


def test_end_of_exam_and_repeated_header_are_not_part_of_the_last_question():
    """Bà Rịa - Vũng Tàu: 'HẾT', the exam header again and a '1.B | 2.C …' key before the solutions."""
    res = split(L(EXAM + """
🙢 **HẾT** 🙠
**SỞ GIÁO DỤC & ĐÀO TẠO TỈNH BÀ RỊA - VŨNG TÀU**
**KÌ THI TỐT NGHIỆP TRUNG HỌC PHỔ THÔNG**
**NĂM HỌC 2024-2025**
**MÔN THI: TOÁN - Lớp 12**
Thời gian làm bài: 90 phút, không kể thời gian giao đề
Mã đề thi.....
**HƯỚNG DẪN GIẢI CHI TIẾT**
**PHẦN I: CÂU TRẮC NGHIỆM NHIỀU PHƯƠNG ÁN LỰA CHỌN**
**1.B** | **2.C** | **3.A**
**Câu 1:** Giá trị của $u_{3}$ bằng
**A.** 9. **B.** -16. **C.** 7. **D.** -8.
**Lời giải**
Ta có …
**PHẦN III: CÂU TRẮC NGHIỆM TRẢ LỜI NGẮN**
**Câu 2:** Tính $D=3a+6b$.
Vậy $D=7,2$
---HẾT---
"""))
    qs = by_key(res)
    last = qs[("3", 2)]
    assert last.stem == "Tính $D=3a+6b$." and "SỞ" not in last.raw and "1.B" not in last.raw
    assert qs[("1", 1)].answer == {"key": "B"} and qs[("1", 2)].answer == {"key": "C"}  # from the key row
    assert "HẾT" not in last.solution and last.solution.endswith("7,2$")
    assert any("NĂM HỌC" in p for p in res.preamble)
