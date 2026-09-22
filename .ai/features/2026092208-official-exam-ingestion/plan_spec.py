# Source spec for 04-units-of-work — regenerate with:
#   python3 scripts/gen_plan.py .ai/features/2026092208-official-exam-ingestion .ai/features/2026092208-official-exam-ingestion/plan_spec.py
API = "apps/api"
WEB = "apps/web"

UOWS = [
    dict(dod_done=True, id="UOW-01", slug="formulas-figures", title="MathType formulas become LaTeX, WMF/EMF figures become PNG",
         requirements=["US-01", "US-02"], risk="high",
         demo=["Upload the Nguyễn Khuyến .docx → review queue shows Câu 1 with KaTeX $\\left(u_{n}\\right)$, $u_{1}=-1$",
               "Câu 4 shows the cube figure as PNG; Phần II Câu 1 graph as PNG",
               "Document log lists 475 equations, 0 failed"],
         in_scope=["mtef.py reader + LaTeX", "docx token swap", "vector_images.py + Dockerfile", "document_store conversion"]),
    dict(dod_done=True, id="UOW-02", slug="thpt-layout", title="THPT 2025 layout: per-part answer tables, verdicts, header-less solutions; golden set of 18",
         requirements=["US-03"], depends_on=["UOW-01"], risk="high",
         demo=["Import d01 → Phần III Câu 1 answer 3 from the per-part table, solution attached",
               "Import Lương Tài 2 (no HƯỚNG DẪN GIẢI title) → 22 questions, not 44",
               "golden_live.py over the 18 files prints 396/396, answers ≥ 98 %"],
         in_scope=["Splitter rules + table tests", "Golden expectations + live runner"]),
    dict(dod_done=True, id="UOW-03", slug="header-upload", title="Header metadata suggestions and multi-file upload",
         requirements=["US-04"], depends_on=["UOW-01"], risk="medium",
         demo=["Drop the 18 files at once → 18 rows queued; dropping one again → 'đã có'",
               "A parsed document shows Nguồn: Sở GD Ninh Bình, 2024-2025, Toán, Thi thử lần 1, 90 phút",
               "Its questions are Toán, lớp 12, Thi thử, tagged with the source"],
         in_scope=["header.py + apply in pipeline", "PATCH /documents/{id}", "UploadForm multi-file", "Detected metadata on the document"]),
    dict(dod_done=True, id="UOW-04", slug="exam-from-document", title="Tạo đề từ tài liệu",
         requirements=["US-05"], depends_on=["UOW-02"], risk="low",
         demo=["Approve a document's questions → 'Tạo đề từ tài liệu' → exam with 12/4/6 in order, 10 điểm",
               "A rejected question is skipped and reported"],
         in_scope=["POST /documents/{id}/exam", "Button on the document"]),
]

T = []
def t(**kw):
    T.append(kw)

t(id="T-01-01", uow="UOW-01", title="MTEF v5 reader → LaTeX with template/char tables and fixtures",
  layer="domain", estimate="4h", verifies=["AC-01", "AC-02"], tests=[f"{API}/tests/test_mtef.py"],
  touches=[f"{API}/app/ingestion/mtef.py", f"{API}/tests/fixtures/mtef", f"{API}/pyproject.toml"],
  assumptions=["A-02"], context="ADR-01. Prototype exists; add tests from corpus objects and fix text-function runs.",
  done_when=["Template table tests", "Corpus fixtures convert", "Unconvertible → None"])
t(id="T-01-02", uow="UOW-01", title="docx: swap MathType objects for tokens before Pandoc; warnings",
  layer="domain", estimate="2h", depends_on=["T-01-01"], verifies=["AC-01", "AC-02"], tests=[f"{API}/tests/test_docx_mathtype.py"],
  touches=[f"{API}/app/ingestion/docx.py", f"{API}/app/ingestion/pipeline.py"], context="ADR-02. Pictures inside a line of text stay inline (formula pictures); a label after a picture starts a new line.",
  done_when=["$…$ in lines", "Failed count warning", "Emphasis around formulas kept"])
t(id="T-01-03", uow="UOW-01", title="WMF/EMF → PNG via LibreOffice + pypdfium2; Dockerfile; document_store",
  layer="infra", estimate="3h", verifies=["AC-03"], tests=[f"{API}/tests/test_vector_images.py"],
  touches=[f"{API}/app/ingestion/vector_images.py", f"{API}/app/ingestion/assets.py", f"{API}/Dockerfile"],
  assumptions=["A-03"], context="ADR-03.", done_when=["PNG trimmed", "Missing soffice → warning", "Image rebuilt"])
t(id="T-02-01", uow="UOW-02", title="Splitter: per-part answer tables in solutions, lower-case verdicts, header-less solution pass, Cyrillic labels, method headings",
  layer="domain", estimate="4h", depends_on=["T-01-02"], verifies=["AC-04", "AC-05", "AC-06", "AC-07"], tests=[f"{API}/tests/test_splitter_thpt.py", f"{API}/tests/test_splitter.py"],
  touches=[f"{API}/app/ingestion/splitter.py", f"{API}/app/ingestion/lines.py"], assumptions=["A-04"], context="ADR-04.",
  done_when=["Table tests", "Old splitter tests green"])
t(id="T-02-02", uow="UOW-02", title="Golden set: 18 reference files, expectations from their tables, live runner report",
  layer="test", estimate="4h", depends_on=["T-02-01", "T-01-03"], verifies=["AC-08"], tests=[f"{API}/tests/test_golden_official.py"],
  touches=[f"{API}/tests/golden/official_expected.json", f"{API}/tests/test_golden_official.py", "scripts/golden_live.py"],
  assumptions=["A-01", "A-08"], context="Runs the extractor + splitter on the files when EXAMIN_DIR is set, otherwise skipped.",
  done_when=["396/396", "Answers ≥ 98 %", "Solutions", "No WMF"])
t(id="T-03-01", uow="UOW-03", title="Header metadata detection, applied to empty meta before persist; PATCH /documents/{id}",
  layer="api", estimate="3h", depends_on=["T-01-02"], verifies=["AC-09"], tests=[f"{API}/tests/test_header_meta.py"],
  touches=[f"{API}/app/ingestion/header.py", f"{API}/app/ingestion/pipeline.py", f"{API}/app/routers/documents.py", f"{API}/app/services/documents.py", f"{API}/app/schemas/documents.py"],
  assumptions=["A-05"], context="ADR-05.", done_when=["Detect", "Apply", "Edit meta"])
t(id="T-03-02", uow="UOW-03", title="UploadForm: many files with per-file status; document shows detected metadata",
  layer="web", estimate="3h", depends_on=["T-03-01"], verifies=["AC-10", "AC-09"], tests=[f"{WEB}/src/__tests__/documents.test.tsx"],
  touches=[f"{WEB}/src/components/documents/UploadForm.tsx", f"{WEB}/src/components/documents/DocumentMetaFields.tsx", f"{WEB}/src/components/documents/DocumentInfo.tsx", f"{WEB}/src/app/(app)/org/documents/page.tsx", f"{WEB}/src/lib/types.ts"],
  assumptions=["A-07"], context="", done_when=["Multi-file", "Duplicate row", "Detected shown"])
t(id="T-04-01", uow="UOW-04", title="POST /documents/{id}/exam: draft exam in part/number order, skipped count",
  layer="api", estimate="2h", depends_on=["T-02-01"], verifies=["AC-11", "AC-12"], tests=[f"{API}/tests/test_exam_from_document.py"],
  touches=[f"{API}/app/services/exams.py", f"{API}/app/routers/documents.py"], assumptions=["A-06"], context="",
  done_when=["Order", "Points", "Skipped"])
t(id="T-04-02", uow="UOW-04", title="'Tạo đề từ tài liệu' button → opens the new exam",
  layer="web", estimate="1h", depends_on=["T-04-01"], verifies=["AC-11"], tests=[f"{WEB}/src/__tests__/documents.test.tsx"],
  touches=[f"{WEB}/src/components/documents/DocumentDetail.tsx", f"{WEB}/src/app/(app)/org/documents/[id]/page.tsx"], context="Page body moved to DocumentDetail so it can be tested.", done_when=["Button", "Toast with skipped"])

TICKETS = T
