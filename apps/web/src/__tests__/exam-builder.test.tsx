import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BlueprintEditor } from "@/components/page-components/ExamDetail/BlueprintEditor/BlueprintEditor";
import { ExamDetailPage } from "@/components/page-components/ExamDetail/ExamDetailPage";
import { ExamQuestions } from "@/components/page-components/ExamDetail/ExamQuestions/ExamQuestions";
import { ExamQuestionsTable } from "@/components/page-components/ExamDetail/ExamQuestionsTable/ExamQuestionsTable";
import type { Exam, ExamQuestion } from "@/interfaces/exam.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { movedTo, swapped } from "@/lib/page-libs/exam-detail/order";
import { lastBody, mockFetch, renderWithQuery, route, searchPage } from "./helpers";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const topics: Topic[] = [{ id: "ds", subject_id: "s", parent_id: null, name: "Đại số", level_kind: "strand", grade: null, path: "a", depth: 1, sort: 0, child_count: 0 }];
const eq = (n: number, section = "I"): ExamQuestion => ({ id: `q${n}`, type: "mcq", stem: `Câu ${n}`, options: [], answer: null, solution: "", difficulty: null,
  grade: null, status: "approved", number: n, part: null, confidence: 1, issues: [], parse_method: null, parse_model: null, answer_source: null,
  subject_id: null, semester_code: null, exam_kind: null, topics: [], tags: [], position: n, section, points: 0.25, row: 0 });
const exam = (o: Partial<Exam> = {}): Exam => ({
  id: "e1", title: "Kiểm tra 15 phút", subject_id: null, grade: 10, description: "",
  settings: { points_by_type: { mcq: 0.25, true_false: 1, short_answer: 0.5, essay: 1 }, scale_to: 10 },
  blueprint: [], source: "manual", question_count: 3, total_points: 0.75, created_at: "2026-09-22T00:00:00Z", questions: [eq(1), eq(2), eq(3)], ...o,
});

beforeEach(() => setUrl("/org/exams/e1"));
afterEach(() => vi.unstubAllGlobals());

// the page loads the exam, its subject's topics and tags, the classes and the exam's assignments
const pageRoutes = (e: Exam) => [
  route("GET", "/api/exams/e1", e),
  route("GET", "/api/topics", topics),
  route("POST", "/api/tags/search", searchPage([])),
  route("POST", "/api/classes/search", searchPage([])),
  route("POST", "/api/assignments/search", searchPage([])),
];

describe("exam builder", () => {
  it("blueprint rows need a topic, then generate", async () => {
    const onGenerate = vi.fn();
    render(<BlueprintEditor initial={[]} topics={topics} tags={[]} shortfalls={[{ row: 0, missing: 2 }]} onGenerate={onGenerate} />);
    expect(screen.getByRole("button", { name: "Tạo đề theo ma trận" })).toBeDisabled();
    expect(screen.getByTestId("row-0")).toHaveTextContent("thiếu 2 câu");
    await userEvent.click(screen.getByRole("button", { name: "Chọn chuyên đề…" }));
    await userEvent.click(within(screen.getByRole("tree", { name: "Cây chuyên đề" })).getByText("Đại số"));
    fireEvent.change(screen.getByLabelText("Số câu"), { target: { value: "6" } });
    await userEvent.click(screen.getByRole("button", { name: "Tạo đề theo ma trận" }));
    expect(onGenerate).toHaveBeenCalledWith([{ type: "mcq", count: 6, topic_id: "ds" }]);
  });

  it("question list: sections, swap, remove, points", async () => {
    const onSaveOrder = vi.fn(), onSwap = vi.fn(), onRemove = vi.fn(), onPoints = vi.fn();
    render(<ExamQuestions questions={[eq(1), eq(2), eq(3, "II")]} onSaveOrder={onSaveOrder} onSwap={onSwap} onRemove={onRemove} onPoints={onPoints} />);
    expect(screen.getByText("Phần I")).toBeInTheDocument();
    expect(screen.getByText("Phần II")).toBeInTheDocument();
    await userEvent.click(within(screen.getByTestId("eq-1")).getByRole("button", { name: "Đổi câu" }));
    expect(onSwap).toHaveBeenCalledWith("q1");
    await userEvent.click(within(screen.getByTestId("eq-2")).getByRole("button", { name: "Bỏ" }));
    expect(onRemove).toHaveBeenCalledWith("q2");
    const pts = screen.getByLabelText("Điểm câu 3");
    fireEvent.change(pts, { target: { value: "1" } });
    fireEvent.blur(pts);
    expect(onPoints).toHaveBeenCalledWith("q3", 1);
  });

  it("reorders on a draft and saves once: swap with a chosen position, ↑/↓, only inside a part", async () => {
    const onSaveOrder = vi.fn();
    const u = userEvent.setup();
    render(<ExamQuestions questions={[eq(1), eq(2), eq(3), eq(4, "II")]} onSaveOrder={onSaveOrder} onSwap={vi.fn()} onRemove={vi.fn()} onPoints={vi.fn()} />);
    await u.click(screen.getByRole("button", { name: /Sắp xếp thứ tự/ }));
    expect(screen.getByRole("button", { name: /Lưu thứ tự/ })).toBeDisabled();
    await u.click(screen.getByRole("combobox", { name: "Đổi chỗ câu 1 với" }));
    const opts = await screen.findAllByRole("option");
    expect(opts.map((o) => o.textContent)).toEqual(["Đổi chỗ với…", "Câu 2", "Câu 3"]); // not câu 4 (Phần II)
    await u.click(screen.getByRole("option", { name: "Câu 3" }));
    await u.click(screen.getByRole("button", { name: "Đưa câu 1 xuống" }));
    expect(onSaveOrder).not.toHaveBeenCalled(); // nothing saved while editing
    expect(screen.getByRole("button", { name: "Đưa câu 4 lên" })).toBeDisabled();
    await u.click(screen.getByRole("button", { name: /Lưu thứ tự \(3 vị trí đổi\)/ }));
    expect(onSaveOrder).toHaveBeenCalledTimes(1);
    expect(onSaveOrder).toHaveBeenCalledWith(["q2", "q3", "q1", "q4"]);
    expect(movedTo(["a", "b", "c"], "a", "c")).toEqual(["b", "c", "a"]);
    expect(movedTo(["a", "b", "c"], "c", "a")).toEqual(["c", "a", "b"]);
    expect(swapped(["a", "b", "c"], "a", "c")).toEqual(["c", "b", "a"]);
  });

  it("the page generates from the matrix, shows shortfalls and refetches the exam", async () => {
    const f = mockFetch(
      route("POST", "/api/exams/e1/blueprint", { added: 4, shortfalls: [{ row: 0, missing: 2 }], exam: exam() }),
      ...pageRoutes(exam({ blueprint: [{ topic_id: "ds", type: "mcq", count: 6 }] })),
    );
    const u = userEvent.setup();
    renderWithQuery(<ExamDetailPage id="e1" />);
    await u.click(await screen.findByRole("button", { name: "Tạo đề theo ma trận" }));
    await waitFor(() => expect(screen.getByTestId("row-0")).toHaveTextContent("thiếu 2 câu"));
    expect(lastBody(f, "/exams/e1/blueprint")).toEqual({ rows: [{ topic_id: "ds", type: "mcq", count: 6 }] });
    await waitFor(() => expect(f.mock.calls.filter(([url]) => url === "/api/exams/e1")).toHaveLength(2)); // invalidated
  });

  it("the page saves a new order with PUT /order, and default points with PATCH", async () => {
    const f = mockFetch(route("PUT", "/api/exams/e1/order", exam()), route("PATCH", "/api/exams/e1", exam()), ...pageRoutes(exam()));
    const u = userEvent.setup();
    renderWithQuery(<ExamDetailPage id="e1" />);
    await u.click(await screen.findByRole("button", { name: /Sắp xếp thứ tự/ }));
    await u.click(screen.getByRole("button", { name: "Đưa câu 1 xuống" }));
    await u.click(screen.getByRole("button", { name: /Lưu thứ tự/ }));
    await waitFor(() => expect(screen.getByTestId("exam-questions")).toBeInTheDocument());
    const put = f.mock.calls.find(([url, init]) => url === "/api/exams/e1/order" && (init as RequestInit).method === "PUT")!;
    expect(JSON.parse(String((put[1] as RequestInit).body))).toEqual({ question_ids: ["q2", "q1", "q3"] });
    const essay = screen.getByLabelText("Điểm Tự luận");
    fireEvent.change(essay, { target: { value: "2" } });
    fireEvent.blur(essay);
    await waitFor(() => expect(f.mock.calls.some(([url, init]) => url === "/api/exams/e1" && (init as RequestInit)?.method === "PATCH")).toBe(true));
    const patch = f.mock.calls.find(([url, init]) => url === "/api/exams/e1" && (init as RequestInit)?.method === "PATCH")!;
    expect(JSON.parse(String((patch[1] as RequestInit).body))).toEqual({ settings: { points_by_type: { essay: 2 } } });
  });

  it("adds a question found in the bank", async () => {
    const found = { ...eq(9), stem: "Câu trong ngân hàng" };
    const f = mockFetch(route("POST", "/api/questions/search", searchPage([found, { ...eq(1), stem: "Đã trong đề" }])), route("POST", "/api/exams/e1/questions", exam()), ...pageRoutes(exam()));
    const u = userEvent.setup();
    renderWithQuery(<ExamDetailPage id="e1" />);
    await u.type(await screen.findByPlaceholderText("Tìm câu hỏi…"), "parabol");
    await u.click(screen.getByRole("button", { name: "Tìm" }));
    const results = screen.getByTestId("bank-results");
    await within(results).findByText("Câu trong ngân hàng");
    expect(lastBody(f, "/questions/search")).toMatchObject({ page: 1, limit: 10, q: "parabol" });
    expect(within(results).getByRole("button", { name: "Đã có" })).toBeDisabled();
    await u.click(within(results).getByRole("button", { name: "Thêm" }));
    await waitFor(() => expect(lastBody(f, "/exams/e1/questions")).toEqual({ question_ids: ["q9"] }));
  });

  it("the questions table posts /exams/{id}/questions/search with its own filters", async () => {
    const f = mockFetch(route("POST", "/api/exams/e1/questions/search", searchPage([eq(1), eq(2, "II")])));
    setUrl("/org/exams?q.section=II&q.sort=-points");
    renderWithQuery(<ExamQuestionsTable examId="e1" />);
    expect(await screen.findByText("Câu 2")).toBeInTheDocument();
    expect(lastBody(f, "/exams/e1/questions/search")).toEqual({ page: 1, limit: 20, sort: [{ field: "points", desc: true }], filters: { section: { value: "II" } } });
  });
});
