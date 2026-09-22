import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import DocumentsPage from "@/app/(app)/org/documents/page";
import { ParsedQuestionCard } from "@/components/documents/ParsedQuestion";
import { DocumentInfo } from "@/components/documents/DocumentInfo";
import { UploadForm } from "@/components/documents/UploadForm";
import { ThemeProvider } from "@/components/app/ThemeProvider";
import type { ParsedQuestion, SourceDocument, Taxonomy } from "@/lib/types";
import { mockFetch, page, route } from "./helpers";
import { currentUrl, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const taxonomy: Taxonomy = {
  subjects: [{ id: "s-toan", code: "toan", name: "Toán" }],
  grades: [{ id: "g10", level: 10, name: "Lớp 10" }],
  semesters: [{ id: "hk1", code: "hk1", name: "Học kỳ 1" }],
};

const doc = (o: Partial<SourceDocument> = {}): SourceDocument => ({
  id: "d1", filename: "de.docx", mime: "x", size: 1, status: "parsed", error: null,
  meta: { subject_id: "s-toan", grade: 10, semester_code: "hk1", exam_kind: "Giữa kỳ" },
  processing_config: { split_mode: "rule", ocr: "auto", split_models: [], tag_model: null, vision_model: null, threshold: 0.85 },
  page_count: null, question_count: 40, log: [], created_at: "2026-09-22T00:00:00Z", finished_at: null, ...o,
});

afterEach(() => vi.unstubAllGlobals());

async function pick(field: string, option: string) {
  await userEvent.click(screen.getByRole("combobox", { name: field }));
  await userEvent.click(await screen.findByRole("option", { name: option }));
}

describe("documents", () => {
  it("uploads the file with metadata and reports duplicates", async () => {
    const f = mockFetch(route("POST", "/api/documents", { document: doc(), duplicate: true }, 200));
    const onUploaded = vi.fn();
    render(<UploadForm taxonomy={taxonomy} onUploaded={onUploaded} />);
    fireEvent.change(screen.getByTestId("file"), { target: { files: [new File(["x"], "de.docx")] } });
    await pick("Môn", "Toán");
    await pick("Lớp", "Lớp 10");
    await pick("Đợt kiểm tra", "Cuối kỳ 2");
    expect(screen.getByRole("combobox", { name: "Đợt kiểm tra" })).toHaveTextContent("Cuối kỳ 2");
    await userEvent.type(screen.getByLabelText(/Nguồn đề/), "THPT A");
    await userEvent.click(await screen.findByRole("button", { name: "Tải lên và tách câu" }));
    await waitFor(() => expect(onUploaded).toHaveBeenCalledWith(expect.objectContaining({ id: "d1" }), true));
    const form = f.mock.calls.find(([url, init]) => url === "/api/documents" && init?.method === "POST")?.[1]?.body as FormData;
    expect(JSON.parse(String(form.get("meta")))).toMatchObject({ subject_id: "s-toan", grade: 10, semester_code: "hk2", exam_kind: "Cuối kỳ", source_name: "THPT A" });
    expect(screen.getByRole("list", { name: "File đã chọn" })).toHaveTextContent("Đã có — dùng bản cũ");
  });

  it("uploads many files in one go, leaving fields to the exam header", async () => {
    let n = 0;
    const f = mockFetch((url, init) =>
      url === "/api/documents" && init?.method === "POST"
        ? ++n === 2
          ? { status: 200, body: { document: doc({ id: "d2" }), duplicate: true } }
          : { status: 201, body: { document: doc({ id: `d${n}` }), duplicate: false } }
        : undefined,
    );
    const onFinished = vi.fn();
    render(<UploadForm taxonomy={taxonomy} onFinished={onFinished} />);
    expect(screen.getByRole("combobox", { name: "Môn" })).toHaveTextContent("Tự nhận từ đề");
    const files = ["de1.docx", "de2.docx", "de3.pdf", "ghichu.txt"].map((name) => new File(["x"], name));
    fireEvent.change(screen.getByTestId("file"), { target: { files } });
    expect(screen.getByText("Bỏ qua 1 file không phải .docx, .pdf hoặc ảnh")).toBeInTheDocument();
    await userEvent.click(await screen.findByRole("button", { name: "Tải lên 3 file và tách câu" }));
    await waitFor(() => expect(onFinished).toHaveBeenCalled());
    expect(onFinished.mock.calls[0][0]).toHaveLength(3);
    const list = screen.getByRole("list", { name: "File đã chọn" });
    expect(list).toHaveTextContent("de1.docxĐã đưa vào hàng đợi");
    expect(list).toHaveTextContent("de2.docxĐã có — dùng bản cũ");
    expect(JSON.parse(String((f.mock.calls.find(([url, init]) => url === "/api/documents" && init?.method === "POST")?.[1]?.body as FormData).get("meta")))).toEqual({});
  });

  it("asks what to do with files already uploaded: skip the same content, replace a same-name file", async () => {
    const brief = (id: string, filename: string) => ({ id, filename, status: "parsed", question_count: 22, created_at: "2026-09-22T08:45:00Z" });
    const sent: FormData[] = [];
    const f = mockFetch((url, init) => {
      if (url === "/api/documents/check")
        return { body: [{ name: "a.docx", same_file: brief("d-a", "a.docx"), same_name: [] }, { name: "b.docx", same_file: null, same_name: [brief("d-b", "b.docx")] }, { name: "c.docx", same_file: null, same_name: [] }] };
      if (url === "/api/documents" && init?.method === "POST") {
        const form = init.body as FormData;
        sent.push(form);
        return form.get("on_duplicate") === "replace"
          ? { status: 200, body: { document: doc({ id: "d-b" }), duplicate: true, action: "replaced" } }
          : { status: 201, body: { document: doc({ id: "d-c" }), duplicate: false, action: "created" } };
      }
      return undefined;
    });
    const onFinished = vi.fn();
    const u = userEvent.setup();
    render(<ThemeProvider><UploadForm taxonomy={taxonomy} onFinished={onFinished} /></ThemeProvider>);
    fireEvent.change(screen.getByTestId("file"), { target: { files: ["a.docx", "b.docx", "c.docx"].map((n) => new File([n], n)) } });
    expect(await screen.findByText(/Đã có file giống hệt: “a.docx”/)).toBeInTheDocument();
    expect(screen.getByText(/Trùng tên với 1 đề đã tải/)).toBeInTheDocument();
    const check = JSON.parse(String(f.mock.calls.find(([url]) => url === "/api/documents/check")?.[1]?.body));
    expect(check.files.map((x: { sha256: string }) => x.sha256.length)).toEqual([64, 64, 64]);
    expect(screen.getByRole("combobox", { name: "Cách xử lý a.docx" })).toHaveTextContent("Bỏ qua (dùng bản đã có)");
    expect(screen.getByRole("combobox", { name: "Cách xử lý b.docx" })).toHaveTextContent("Ghi đè bản cũ");
    await u.click(screen.getByRole("button", { name: "Tải lên 2 file và tách câu" }));
    await waitFor(() => expect(onFinished).toHaveBeenCalled());
    expect(sent).toHaveLength(2); // a.docx is not sent at all
    expect([sent[0].get("on_duplicate"), sent[0].get("replace_id")]).toEqual(["replace", "d-b"]);
    expect(sent[1].get("on_duplicate")).toBeNull();
    const list = screen.getByRole("list", { name: "File đã chọn" });
    expect(list).toHaveTextContent("a.docxĐã bỏ qua");
    expect(list).toHaveTextContent("b.docxĐã ghi đè — đang tách lại");
  });

  it("requires a file and shows server field errors", async () => {
    mockFetch(route("POST", "/api/documents", { error: { code: "unsupported_file", message: "Chỉ hỗ trợ", fields: { file: "Lưu lại dưới dạng .docx" } } }, 422));
    render(<UploadForm taxonomy={taxonomy} onUploaded={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: "Tải lên và tách câu" }));
    expect(screen.getByText("Chọn file đề")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("file"), { target: { files: [new File(["x"], "old.doc")] } });
    await userEvent.click(await screen.findByRole("button", { name: "Tải lên và tách câu" }));
    expect((await screen.findAllByText("Lưu lại dưới dạng .docx")).length).toBeGreaterThan(0);
  });

  it("lists documents from the server with status and metadata, polling while one is processing", async () => {
    setUrl("/org/documents");
    const fetch = mockFetch(
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", "/api/org/settings/ingestion", doc().processing_config),
      route("GET", /^\/api\/ai-models\?/, page([])),
      route("GET", /^\/api\/documents\?/, page([doc(), doc({ id: "d2", filename: "b.pdf", status: "processing" })])),
    );
    render(<DocumentsPage />);
    const row = (await screen.findByText("de.docx")).closest("tr")!;
    await waitFor(() => expect(row).toHaveTextContent("Toán · Lớp 10 · Giữa kỳ 1"));
    expect(row).toHaveTextContent("Đã tách · 40 câu");
    expect(screen.getByText("b.pdf").closest("tr")).toHaveTextContent("Đang xử lý");
    const count = () => fetch.mock.calls.filter(([u]) => String(u).startsWith("/api/documents?")).length;
    const before = count();
    await waitFor(() => expect(count()).toBeGreaterThan(before), { timeout: 3000 });
  });

  it("shows what the header said and saves edited metadata", async () => {
    const f = mockFetch(route("PATCH", "/api/documents/d1", doc()));
    const onSaved = vi.fn();
    const d = doc({ meta: { subject_id: "s-toan", grade: 12, exam_kind: "Thi thử", source_name: "Sở GD&ĐT Ninh Bình",
      detected: { issuer: "Sở GD&ĐT Ninh Bình", school_year: "2024-2025", subject_name: "Toán", grade: 12, exam_kind: "Thi thử", attempt: 1, duration: 90 } } });
    render(<ThemeProvider><DocumentInfo doc={d} taxonomy={taxonomy} onSaved={onSaved} /></ThemeProvider>);
    expect(screen.getByTestId("document-info")).toHaveTextContent("Sở GD&ĐT Ninh Bình · 2024-2025 · Toán · Lớp 12 · Thi thử lần 1 · 90 phút");
    await userEvent.click(screen.getByRole("button", { name: "Sửa thông tin" }));
    await pick("Lớp", "Lớp 10");
    await userEvent.click(screen.getByRole("button", { name: "Lưu" }));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    const body = JSON.parse(String(f.mock.calls[0][1]?.body));
    expect(body.meta).toMatchObject({ grade: 10, source_name: "Sở GD&ĐT Ninh Bình" });
    expect(body.meta.detected).toBeUndefined();
  });

  it("parsed question card shows confidence, method and issues", () => {
    const q: ParsedQuestion = {
      id: "q", type: "mcq", stem: "Đề", options: [{ label: "A", content: "1" }], answer: null, solution: "", difficulty: null, grade: 10,
      status: "draft", number: 7, part: "1", confidence: 0.4, issues: ["thiếu phương án", "thiếu đáp án"], parse_method: "rule",
      parse_model: null, answer_source: null, subject_id: null, semester_code: null, exam_kind: null, topics: [], tags: [],
    };
    render(<ParsedQuestionCard q={q} />);
    const card = screen.getByTestId("pq-1-7");
    expect(card).toHaveTextContent("Phần I · Câu 7");
    expect(card).toHaveTextContent("Tin cậy 40%");
    expect(card).toHaveTextContent("thiếu phương án");
  });
});

describe("document page", () => {
  it("creates an exam from the document and opens it", async () => {
    const { DocumentDetail } = await import("@/components/documents/DocumentDetail");
    const f = mockFetch(
      route("GET", "/api/documents/d1", doc()),
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", "/api/documents/d1/questions", []),
      route("POST", "/api/documents/d1/exam", { exam_id: "e9", added: 21, skipped: 1 }, 201),
    );
    render(<ThemeProvider><DocumentDetail id="d1" /></ThemeProvider>);
    await userEvent.click(await screen.findByRole("button", { name: "Tạo đề từ tài liệu" }));
    expect(await screen.findByText("Đã tạo đề thi với 21 câu — bỏ qua 1 câu chưa duyệt")).toBeInTheDocument();
    expect(currentUrl()).toBe("/org/exams/e9");
    expect(f.mock.calls.some(([u, i]) => u === "/api/documents/d1/exam" && i?.method === "POST")).toBe(true);
  });
});
