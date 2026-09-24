# python3 scripts/gen_plan.py .ai/features/2026092403-blueprint-truth .ai/features/2026092403-blueprint-truth/plan_spec.py
WEB = "apps/web"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="row-count", title="Con số của một dòng ma trận là con số lệnh tạo đề sẽ dùng",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["Dòng trên chuyên đề Mệnh đề, chọn Trắc nghiệm: số đọc 7 chứ không phải 14",
               "Đổi sang Đúng/Sai: số đổi theo, không cần tạo đề mới biết",
               "Đòi 10 câu khi chỉ có 7: màn hình nói chuyên đề có 14, hợp dòng này 7"],
         in_scope=["per-row count", "shortfall explains"]),
    dict(id="UOW-02", slug="no-labels", title="Bỏ nhãn xếp hạng, và nút chế độ xem có icon",
         requirements=["US-03"], risk="low",
         demo=["Ba màn theo chuyên đề: thứ tự giữ nguyên, không còn chữ yếu nhất",
               "Nút Một câu / Toàn đề có icon và tooltip"],
         in_scope=["remove ranking labels", "mode toggle icons"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Mỗi dòng hỏi số câu của chính bộ lọc của nó", layer="web", estimate="4h",
  verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-02"],
  tests=[f"{S}/__tests__/exam-builder.test.tsx"],
  touches=[f"{S}/hooks/page-hooks/exam-detail/use-blueprint-editor.ts",
           f"{S}/components/page-components/ExamDetail/BlueprintEditor/BlueprintEditor.tsx",
           f"{S}/hooks/react-query/use-query-question.ts"],
  context="ADR-01: POST /questions/search {topic_id, type, difficulty, status: usable, limit: 1} rồi đọc total.",
  done_when=["Số theo đúng bộ lọc của dòng", "Đổi loại câu hay mức độ thì số tính lại",
             "Bằng đúng số lệnh tạo đề lấy được"])
t(id="T-01-02", uow="UOW-01", title="Thiếu câu thì nói rõ vì sao", layer="web", estimate="2h",
  depends_on=["T-01-01"], verifies=["AC-03"], assumptions=["A-03"],
  tests=[f"{S}/__tests__/exam-builder.test.tsx"],
  touches=[f"{S}/components/page-components/ExamDetail/BlueprintEditor/BlueprintEditor.tsx"],
  context="Có cả hai con số rồi: tổng của chuyên đề và số hợp bộ lọc của dòng.",
  done_when=["Nêu cả hai con số", "Dòng rỗng vẫn đỏ như cũ", "Không đổi mã lỗi nào"])
t(id="T-02-01", uow="UOW-02", title="Bỏ nhãn xếp hạng ở ba màn", layer="web", estimate="2h",
  verifies=["AC-04"], assumptions=["A-04"],
  tests=[f"{S}/__tests__/result.test.tsx", f"{S}/__tests__/my-stats.test.tsx"],
  touches=[f"{S}/components/page-components/AttemptResult/ResultView/ResultView.tsx",
           f"{S}/components/page-components/ClassDetail/ClassOverview/ClassOverview.tsx",
           f"{S}/components/page-components/MyStats/MyStatsPage.tsx"],
  context="ADR-02: giữ nguyên thứ tự sắp xếp, chỉ bỏ cách gọi tên.",
  done_when=["Ba chỗ không còn chữ xếp hạng", "Thứ tự không đổi", "Test nào ghim chữ cũ thì sửa theo"])
t(id="T-02-02", uow="UOW-02", title="Nút chế độ xem có icon và tooltip", layer="web", estimate="2h",
  verifies=["AC-05"], assumptions=["A-05"],
  tests=[f"{S}/__tests__/exam-runner.test.tsx"],
  touches=[f"{S}/components/page-components/ExamRunner/Runner/Runner.tsx"],
  context="ADR-03: icon cộng chữ ở màn rộng, tooltip ở mọi màn.",
  done_when=["Mỗi chế độ một icon", "Tooltip nói rõ chế độ làm gì", "Tên chế độ vẫn đọc được bằng trình đọc màn hình"])
TICKETS = T
