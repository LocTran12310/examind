import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import DocumentsPage from "@/app/(app)/org/documents/page";
import { ParsedQuestionCard } from "@/components/documents/ParsedQuestion";
import { UploadForm } from "@/components/documents/UploadForm";
import type { ParsedQuestion, SourceDocument, Taxonomy } from "@/lib/types";
import { mockFetch, page, route } from "./helpers";
import { setUrl } from "./router-mock";

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

describe("documents", () => {
  it("uploads the file with metadata and reports duplicates", async () => {
    const f = mockFetch(route("POST", "/api/documents", { document: doc(), duplicate: true }, 200));
    const onUploaded = vi.fn();
    render(<UploadForm taxonomy={taxonomy} onUploaded={onUploaded} />);
    fireEvent.change(screen.getByTestId("file"), { target: { files: [new File(["x"], "de.docx")] } });
    await userEvent.selectOptions(screen.getByLabelText("Lớp"), "10");
    await userEvent.selectOptions(screen.getByLabelText("Đợt kiểm tra"), "hk2|Cuối kỳ");
    await userEvent.type(screen.getByLabelText(/Nguồn đề/), "THPT A");
    await userEvent.click(screen.getByRole("button", { name: "Tải lên và tách câu" }));
    await waitFor(() => expect(onUploaded).toHaveBeenCalledWith(expect.objectContaining({ id: "d1" }), true));
    const form = f.mock.calls[0][1]?.body as FormData;
    expect(JSON.parse(String(form.get("meta")))).toMatchObject({ subject_id: "s-toan", grade: 10, semester_code: "hk2", exam_kind: "Cuối kỳ", source_name: "THPT A" });
  });

  it("requires a file and shows server field errors", async () => {
    mockFetch(route("POST", "/api/documents", { error: { code: "unsupported_file", message: "Chỉ hỗ trợ", fields: { file: "Lưu lại dưới dạng .docx" } } }, 422));
    render(<UploadForm taxonomy={taxonomy} onUploaded={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: "Tải lên và tách câu" }));
    expect(screen.getByText("Chọn file đề")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("file"), { target: { files: [new File(["x"], "old.doc")] } });
    await userEvent.click(screen.getByRole("button", { name: "Tải lên và tách câu" }));
    expect(await screen.findByText("Lưu lại dưới dạng .docx")).toBeInTheDocument();
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
