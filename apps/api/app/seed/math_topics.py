"""Toán 6–12 knowledge tree template (chương trình GDPT 2018), copied into every new org.

Each node: (name, level_kind, grade | None, children).
"""

MATH_TREE = [
    ("Số học", "strand", None, [
        ("Số tự nhiên và tính chia hết", "topic", 6, []),
        ("Số nguyên tố, ƯCLN và BCNN", "topic", 6, []),
        ("Phân số và số thập phân", "topic", 6, []),
        ("Số hữu tỉ và số thực", "topic", 7, []),
    ]),
    ("Đại số", "strand", None, [
        ("Mệnh đề và tập hợp", "topic", 10, [
            ("Mệnh đề", "subtopic", 10, []),
            ("Tập hợp và các phép toán", "subtopic", 10, []),
        ]),
        ("Bất phương trình bậc nhất hai ẩn", "topic", 10, []),
        ("Hàm số bậc hai và đồ thị", "topic", 10, [
            ("Tìm đỉnh và trục đối xứng parabol", "type", 10, []),
            ("Sự biến thiên của hàm số bậc hai", "type", 10, []),
            ("Dấu của tam thức bậc hai", "subtopic", 10, []),
        ]),
        ("Phương trình quy về phương trình bậc hai", "topic", 10, []),
        ("Đại số tổ hợp", "topic", 10, [
            ("Quy tắc đếm", "subtopic", 10, []),
            ("Hoán vị, chỉnh hợp, tổ hợp", "subtopic", 10, []),
            ("Nhị thức Newton", "subtopic", 10, []),
        ]),
        ("Hàm số lượng giác và phương trình lượng giác", "topic", 11, [
            ("Giá trị lượng giác và công thức lượng giác", "subtopic", 11, []),
            ("Phương trình lượng giác cơ bản", "subtopic", 11, []),
        ]),
        ("Dãy số, cấp số cộng, cấp số nhân", "topic", 11, []),
        ("Hàm số mũ và hàm số logarit", "topic", 11, [
            ("Lũy thừa với số mũ thực", "subtopic", 11, []),
            ("Logarit", "subtopic", 11, []),
            ("Phương trình mũ và logarit", "subtopic", 11, []),
            ("Bất phương trình mũ và logarit", "subtopic", 11, []),
        ]),
    ]),
    ("Giải tích", "strand", None, [
        ("Giới hạn và hàm số liên tục", "topic", 11, []),
        ("Đạo hàm", "topic", 11, []),
        ("Ứng dụng đạo hàm để khảo sát hàm số", "topic", 12, [
            ("Tính đơn điệu của hàm số", "subtopic", 12, []),
            ("Cực trị của hàm số", "subtopic", 12, []),
            ("Giá trị lớn nhất, nhỏ nhất", "subtopic", 12, []),
            ("Đường tiệm cận", "subtopic", 12, []),
            ("Đọc đồ thị hàm số", "subtopic", 12, []),
        ]),
        ("Nguyên hàm", "topic", 12, [
            ("Nguyên hàm cơ bản", "subtopic", 12, []),
            ("Phương pháp đổi biến số", "subtopic", 12, []),
        ]),
        ("Tích phân", "topic", 12, [
            ("Tính tích phân", "subtopic", 12, []),
            ("Ứng dụng tích phân tính diện tích", "subtopic", 12, []),
            ("Ứng dụng tích phân tính thể tích", "subtopic", 12, []),
        ]),
    ]),
    ("Hình học", "strand", None, [
        ("Hệ thức lượng trong tam giác", "topic", 10, []),
        ("Vectơ", "topic", 10, [
            ("Các phép toán vectơ", "subtopic", 10, []),
            ("Tích vô hướng của hai vectơ", "subtopic", 10, []),
        ]),
        ("Phương pháp tọa độ trong mặt phẳng", "topic", 10, [
            ("Phương trình đường thẳng", "subtopic", 10, []),
            ("Phương trình đường tròn", "subtopic", 10, []),
            ("Ba đường conic", "subtopic", 10, []),
        ]),
        ("Quan hệ song song trong không gian", "topic", 11, []),
        ("Quan hệ vuông góc trong không gian", "topic", 11, [
            ("Góc trong không gian", "subtopic", 11, []),
            ("Khoảng cách trong không gian", "subtopic", 11, []),
        ]),
        ("Khối đa diện và thể tích", "topic", 12, [
            ("Thể tích khối chóp", "type", 12, []),
            ("Thể tích khối lăng trụ", "type", 12, []),
        ]),
        ("Tọa độ trong không gian Oxyz", "topic", 12, [
            ("Phương trình mặt phẳng", "subtopic", 12, []),
            ("Phương trình đường thẳng trong không gian", "subtopic", 12, []),
            ("Phương trình mặt cầu", "subtopic", 12, []),
        ]),
    ]),
    ("Thống kê và Xác suất", "strand", None, [
        ("Thống kê", "topic", None, [
            ("Số đặc trưng của mẫu số liệu không ghép nhóm", "subtopic", 10, []),
            ("Số đặc trưng của mẫu số liệu ghép nhóm", "subtopic", 11, []),
        ]),
        ("Xác suất", "topic", None, [
            ("Xác suất cổ điển", "subtopic", 10, []),
            ("Xác suất có điều kiện và công thức Bayes", "subtopic", 12, []),
        ]),
    ]),
]
