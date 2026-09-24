S = "apps/web/src"
UOWS = [
    dict(id="UOW-01", slug="phrase-mode", title="Phương án được đọc như một cụm, không như một tài liệu",
         requirements=["US-01"], risk="low",
         demo=["Câu có phương án 108. / 31. / 13. / 36. hiện đủ bốn số ở màn duyệt và màn làm bài",
               "Phương án có công thức, chữ, hình không đổi",
               "Đề bài có danh sách đánh số vẫn là danh sách"],
         in_scope=["phrase mode in Markdown", "options use it"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Chế độ cụm cho Markdown", layer="web", estimate="3h",
  verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-03"],
  tests=[f"{S}/__tests__/markdown.test.tsx"],
  touches=[f"{S}/components/common/Markdown/Markdown.tsx", f"{S}/lib/common/markdown.ts"],
  context="ADR-01, ADR-02. Thoát dấu mở đầu cấu trúc khối ở đầu mỗi dòng; chữ hiện ra không đổi.",
  done_when=["9. hiện là 9.", "Công thức, chữ, hình không đổi", "Hàm thoát là hàm thuần, có test riêng"])
t(id="T-01-02", uow="UOW-01", title="Phương án dùng chế độ cụm, đề bài thì không", layer="web", estimate="2h",
  depends_on=["T-01-01"], verifies=["AC-01", "AC-03"], assumptions=["A-02"],
  tests=[f"{S}/__tests__/question-view.test.tsx"],
  touches=[f"{S}/components/common/QuestionView/QuestionView.tsx"],
  context="o.content là chỗ duy nhất trong app render nội dung phương án.",
  done_when=["Phương án đi qua chế độ cụm", "Đề bài và lời giải giữ đường cũ",
             "Có test cho một đề bài có danh sách thật"])
TICKETS = T
