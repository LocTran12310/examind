import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BlueprintEditor } from "@/components/page-components/ExamDetail/BlueprintEditor/BlueprintEditor";
import { ExamDetailPage } from "@/components/page-components/ExamDetail/ExamDetailPage";
import { ExamQuestions } from "@/components/page-components/ExamDetail/ExamQuestions/ExamQuestions";
import { ExamQuestionsTable } from "@/components/page-components/ExamDetail/ExamQuestionsTable/ExamQuestionsTable";
import { ExamWeighting } from "@/components/page-components/ExamDetail/ExamWeighting/ExamWeighting";
import { SECTION_OF_TYPE } from "@/constants/exam.constant";
import type { Exam, ExamQuestion } from "@/interfaces/exam.interface";
import type { QuestionType } from "@/interfaces/question.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { movedTo, swapped } from "@/lib/page-libs/exam-detail/order";
import { lastBody, mockFetch, renderWithQuery, route, searchPage } from "./helpers";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const topics: Topic[] = [{ id: "ds", subject_id: "s", parent_id: null, name: "Đại số", level_kind: "strand", grade: null, path: "a", depth: 1, sort: 0, child_count: 0 }];
/** `POST /questions/facets`: the counts the pickers show beside a topic (pickers-builder ADR-01) */
const facets = (t: Record<string, number>) => ({ subjects: {}, topics: t, types: {}, difficulties: {}, grades: {}, periods: {}, school_years: {}, tags: {} });
/** `POST /questions/search`: the pool of one matrix row, keyed by the filters that row asks with — "mcq",
 *  "true_false/nb"… (blueprint-truth ADR-01). Only `total` is read, so the page itself stays empty. */
const rowPool = (totals: Record<string, number>) => (url: string, init?: RequestInit) => {
  if (url !== "/api/questions/search" || (init?.method ?? "GET") !== "POST") return undefined;
  const b = JSON.parse(String(init?.body)) as { type?: string; difficulty?: string };
  return { body: searchPage([], totals[[b.type, b.difficulty].filter(Boolean).join("/")] ?? 0) };
};
const eq = (n: number, section = "I"): ExamQuestion => ({ id: `q${n}`, type: "mcq", stem: `Câu ${n}`, options: [], answer: null, solution: "", difficulty: null,
  grade: null, status: "approved", number: n, part: null, confidence: 1, issues: [], parse_method: null, parse_model: null, answer_source: null,
  subject_id: null, semester_code: null, exam_kind: null, topics: [], tags: [], position: n, section, points: 0.25, row: 0 });
const exam = (o: Partial<Exam> = {}): Exam => ({
  id: "e1", title: "Kiểm tra 15 phút", subject_id: null, grade: 10, description: "",
  settings: { points_by_type: { mcq: 0.25, true_false: 1, short_answer: 0.5, essay: 1 }, scale_to: 10 },
  blueprint: [], source: "manual", question_count: 3, total_points: 0.75, created_at: "2026-09-22T00:00:00Z", questions: [eq(1), eq(2), eq(3)], ...o,
});

/** a question of a given type, in the part that type belongs to, worth `points` */
const wq = (n: number, type: QuestionType, points: number): ExamQuestion => ({ ...eq(n, SECTION_OF_TYPE[type]), type, points });
/** body of the request that went to `url` with `method` */
const sent = (f: { mock: { calls: unknown[][] } }, method: string, url: string) => {
  const call = [...f.mock.calls].reverse().find((c) => c[0] === url && ((c[1] as RequestInit | undefined)?.method ?? "GET") === method);
  return call ? JSON.parse(String((call[1] as RequestInit).body)) : null;
};
/** the cells of one row of the weighting strip */
const cells = (id: string) => within(screen.getByTestId(id)).getAllByRole("cell").map((c) => c.textContent);

beforeEach(() => setUrl("/org/exams/e1"));
afterEach(() => vi.unstubAllGlobals());

// the page loads the exam, its subject's topics and tags, the classes and the exam's assignments
const pageRoutes = (e: Exam, counts: Record<string, number> = {}, pool: Record<string, number> = {}) => [
  route("GET", "/api/exams/e1", e),
  route("GET", /^\/api\/topics(\?|$)/, topics),
  route("GET", "/api/taxonomy", { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [], semesters: [] }),
  route("POST", "/api/questions/facets", facets(counts)),
  rowPool(pool),
  route("POST", "/api/tags/search", searchPage([])),
  route("POST", "/api/classes/search", searchPage([])),
  route("POST", "/api/assignments/search", searchPage([])),
];

describe("exam builder", () => {
  it("blueprint rows need a topic, then generate; the row says how many questions its own filters select", async () => {
    const onGenerate = vi.fn();
    const f = mockFetch(rowPool({ mcq: 7 }), route("POST", "/api/questions/facets", facets({ ds: 14 })));
    renderWithQuery(<BlueprintEditor initial={[]} topics={topics} tags={[]} subjectId="s" shortfalls={[{ row: 0, missing: 2 }]} refusal={null} onEdit={vi.fn()} onGenerate={onGenerate} />);
    expect(screen.getByRole("button", { name: "Tạo đề theo ma trận" })).toBeDisabled();
    expect(screen.getByTestId("row-0")).toHaveTextContent("thiếu 2 câu");
    await userEvent.click(screen.getByRole("button", { name: "Chọn chuyên đề…" }));
    // the picker writes questions beside a topic, not the number of child topics (pickers-builder AC-02, ADR-01)
    await waitFor(() => expect(within(screen.getByRole("tree", { name: "Cây chuyên đề" })).getByTitle("14 câu hỏi")).toBeInTheDocument());
    await userEvent.click(within(screen.getByRole("tree", { name: "Cây chuyên đề" })).getByText("Đại số"));
    // 7, not the 14 the topic holds: the row asks with its own type, the very filter the generator draws through (AC-01)
    await waitFor(() => expect(screen.getByTestId("row-0")).toHaveTextContent("7 câu"));
    expect(lastBody(f, "/questions/search")).toEqual({ page: 1, limit: 1, status: "usable", topic_id: "ds", subject_id: "s", type: "mcq" });
    fireEvent.change(screen.getByLabelText("Số câu"), { target: { value: "6" } });
    await userEvent.click(screen.getByRole("button", { name: "Tạo đề theo ma trận" }));
    expect(onGenerate).toHaveBeenCalledWith([{ type: "mcq", count: 6, topic_id: "ds" }]);
  });

  it("the number follows the row's own type and difficulty, without generating anything (AC-02)", async () => {
    mockFetch(rowPool({ mcq: 7, true_false: 5, "true_false/nb": 2 }), route("POST", "/api/questions/facets", facets({ ds: 14 })));
    const u = userEvent.setup();
    renderWithQuery(<BlueprintEditor initial={[{ topic_id: "ds", type: "mcq", count: 10 }]} topics={topics} tags={[]} subjectId="s" shortfalls={[]} refusal={null} onEdit={vi.fn()} onGenerate={vi.fn()} />);
    await waitFor(() => expect(screen.getByTestId("row-0")).toHaveTextContent("7 câu"));
    await u.click(screen.getByRole("combobox", { name: "Loại câu" }));
    await u.click(await screen.findByRole("option", { name: "Đúng/Sai" }));
    await waitFor(() => expect(screen.getByTestId("row-0")).toHaveTextContent("5 câu"));
    await u.click(screen.getByRole("combobox", { name: "Mức độ" }));
    await u.click(await screen.findByRole("option", { name: "Nhận biết" }));
    await waitFor(() => expect(screen.getByTestId("row-0")).toHaveTextContent("2 câu"));
  });

  it("a row short of questions says how many the topic holds and how many match its own filters (AC-03)", async () => {
    mockFetch(rowPool({ mcq: 7, essay: 14 }), route("POST", "/api/questions/facets", facets({ ds: 14 })));
    const rows = [{ topic_id: "ds", type: "mcq" as const, count: 10 }, { topic_id: "ds", type: "essay" as const, count: 20 }];
    renderWithQuery(<BlueprintEditor initial={rows} topics={topics} tags={[]} subjectId="s" shortfalls={[]} refusal={null} onEdit={vi.fn()} onGenerate={vi.fn()} />);
    // the topic is full, the row's own type is what cuts it — the case "thiếu 3 câu" alone could not tell
    await waitFor(() => expect(screen.getByTestId("row-0")).toHaveTextContent("Chuyên đề có 14 câu dùng được, nhưng chỉ 7 câu là “Trắc nghiệm” — thiếu 3 câu."));
    // nothing narrows this row, so the topic itself is the limit
    expect(screen.getByTestId("row-1")).toHaveTextContent("Chuyên đề chỉ có 14 câu dùng được — thiếu 6 câu.");
  });

  it("a topic that holds nothing is named on its row before generating", async () => {
    mockFetch(rowPool({ mcq: 0 }), route("POST", "/api/questions/facets", facets({ ds: 0 })));
    renderWithQuery(<BlueprintEditor initial={[{ topic_id: "ds", type: "mcq", count: 6 }]} topics={topics} tags={[]} subjectId="s" shortfalls={[]} refusal={null} onEdit={vi.fn()} onGenerate={vi.fn()} />);
    await waitFor(() => expect(screen.getByTestId("row-0")).toHaveTextContent("0 câu"));
    expect(screen.getByTestId("row-0")).toHaveTextContent("Chuyên đề “Đại số” chưa có câu hỏi nào dùng được");
    expect(screen.getByRole("button", { name: "Tạo đề theo ma trận" })).toBeEnabled(); // the server is the authority
  });

  it("the page shows the server's empty-topic refusal, naming the row and the topic", async () => {
    const message = "Dòng 1: chuyên đề “Đại số” không có câu hỏi nào dùng được (0 câu). Chọn chuyên đề khác hoặc bổ sung câu hỏi cho chuyên đề này.";
    mockFetch(
      route("POST", "/api/exams/e1/blueprint", { code: "empty_topic", message, details: { fields: { rows: "Dòng 1", row: 0, topic_id: "ds", topic_name: "Đại số", question_count: 0 } } }, 422),
      ...pageRoutes(exam({ subject_id: "s", blueprint: [{ topic_id: "ds", type: "mcq", count: 6 }] }), { ds: 0 }),
    );
    const u = userEvent.setup();
    renderWithQuery(<ExamDetailPage id="e1" />);
    await u.click(await screen.findByRole("button", { name: "Tạo đề theo ma trận" }));
    expect(await screen.findByTestId("blueprint-refusal")).toHaveTextContent(message);
    // the row it names is marked too, and editing the matrix drops the refusal
    expect(screen.getByTestId("row-0")).toHaveTextContent("0 câu");
    fireEvent.change(screen.getByLabelText("Số câu"), { target: { value: "4" } });
    await waitFor(() => expect(screen.queryByTestId("blueprint-refusal")).not.toBeInTheDocument());
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

  it("the weighting strip states each part, the raw total and the 10-point scale", () => {
    const qs = [
      ...Array.from({ length: 12 }, (_, i) => wq(i + 1, "mcq", 0.25)),
      ...Array.from({ length: 4 }, (_, i) => wq(13 + i, "true_false", 1)),
      ...Array.from({ length: 6 }, (_, i) => wq(17 + i, "short_answer", 0.5)),
    ];
    render(<ExamWeighting exam={exam({ questions: qs, question_count: 22, total_points: 10 })} />);
    expect(cells("weight-I")).toEqual(["Phần ITrắc nghiệm", "12", "0,25", "3"]);
    expect(cells("weight-II")).toEqual(["Phần IIĐúng/Sai", "4", "1", "4"]);
    expect(cells("weight-III")).toEqual(["Phần IIITrả lời ngắn", "6", "0,5", "3"]);
    expect(cells("weight-total")).toEqual(["Cả đề", "22", "tổng thô", "10"]);
    expect(screen.getByTestId("weight-scale")).toHaveTextContent("Tổng thô 10 điểm — đã đúng thang 10, không phải quy đổi.");
    expect(screen.queryByTestId("weight-odd")).not.toBeInTheDocument();
  });

  it("a paper worth less than the scale says what one raw point becomes", () => {
    const qs = Array.from({ length: 10 }, (_, i) => wq(i + 1, "mcq", 0.25));
    render(<ExamWeighting exam={exam({ questions: qs, question_count: 10, total_points: 2.5 })} />);
    expect(cells("weight-I")).toEqual(["Phần ITrắc nghiệm", "10", "0,25", "2,5"]);
    expect(cells("weight-total")).toEqual(["Cả đề", "10", "tổng thô", "2,5"]);
    expect(screen.getByTestId("weight-scale")).toHaveTextContent("Tổng thô 2,5 điểm, quy về thang 10: mỗi điểm thô thành 4 điểm (10 ÷ 2,5).");
  });

  it("a question worth something else than its type default is named", () => {
    const qs = [wq(1, "mcq", 0.25), { ...wq(2, "mcq", 0.5), id: "odd" }, wq(3, "mcq", 0.25)];
    render(<ExamWeighting exam={exam({ questions: qs, question_count: 3, total_points: 1 })} />);
    expect(cells("weight-I")).toEqual(["Phần ITrắc nghiệm", "3", "0,25 (có câu khác)", "1"]);
    const odd = screen.getByTestId("weight-odd");
    expect(odd).toHaveTextContent("1 câu lệch điểm mặc định");
    expect(within(odd).getByRole("link", { name: "Câu 2: 0,5 thay vì 0,25" })).toHaveAttribute("href", "#points-odd");
  });

  it("the page shows the strip and links to the points inputs", async () => {
    mockFetch(...pageRoutes(exam()));
    renderWithQuery(<ExamDetailPage id="e1" />);
    const strip = await screen.findByTestId("exam-weighting");
    expect(cells("weight-total")).toEqual(["Cả đề", "3", "tổng thô", "0,75"]);
    expect(within(strip).getByRole("link", { name: "Sửa điểm mặc định theo loại" })).toHaveAttribute("href", "#diem-mac-dinh");
    expect(within(strip).getByRole("link", { name: "Câu hỏi trong đề" })).toHaveAttribute("href", "#cau-hoi-trong-de");
  });

  it("“Đổi câu” opens the chooser: the bank's own filters, and no question that is already in the exam or of another type", async () => {
    const bank = [
      { ...eq(9), stem: "Câu ngân hàng" },
      { ...eq(2), stem: "Đã trong đề" },
      { ...eq(8), type: "essay" as const, section: "IV", stem: "Câu tự luận" },
    ];
    const f = mockFetch(route("POST", "/api/questions/search", searchPage(bank)), ...pageRoutes(exam({ subject_id: "s" })));
    const u = userEvent.setup();
    renderWithQuery(<ExamDetailPage id="e1" />);
    await u.click(within(await screen.findByTestId("eq-1")).getByRole("button", { name: "Đổi câu" }));
    expect(await screen.findByTestId("swap-dialog")).toHaveTextContent("giữ nguyên vị trí và số điểm này");
    // the chooser searches the bank in the exam's subject, for the type of the position it replaces
    await waitFor(() => expect(lastBody(f, "/questions/search")).toEqual({ page: 1, limit: 20, subject_id: "s", type: "mcq" }));
    expect(within(screen.getByTestId("swap-q9")).getByRole("button", { name: "Chọn" })).toBeEnabled();
    expect(within(screen.getByTestId("swap-q2")).getByRole("button", { name: "Đã có trong đề" })).toBeDisabled();
    expect(within(screen.getByTestId("swap-q8")).getByRole("button", { name: "Khác loại" })).toBeDisabled();
    // searching again keeps the position's type and adds the words typed
    await u.type(screen.getByLabelText("Tìm nội dung"), "parabol");
    await waitFor(() => expect(lastBody(f, "/questions/search")).toEqual({ page: 1, limit: 20, q: "parabol", subject_id: "s", type: "mcq" }));
  });

  it("a chosen question takes the place, the number and the points of the one it replaces", async () => {
    const e = exam({ subject_id: "s", questions: [{ ...eq(1), points: 0.5 }, eq(2), eq(3)] });
    const f = mockFetch(
      route("POST", "/api/questions/search", searchPage([{ ...eq(9), stem: "Câu ngân hàng" }])),
      route("POST", "/api/exams/e1/questions", e),
      route("DELETE", "/api/exams/e1/questions/q1", e),
      route("PUT", "/api/exams/e1/order", e),
      route("PATCH", "/api/exams/e1/questions/q9", e),
      ...pageRoutes(e),
    );
    const u = userEvent.setup();
    renderWithQuery(<ExamDetailPage id="e1" />);
    await u.click(within(await screen.findByTestId("eq-1")).getByRole("button", { name: "Đổi câu" }));
    await u.click(within(await screen.findByTestId("swap-q9")).getByRole("button", { name: "Chọn" }));
    await waitFor(() => expect(sent(f, "PATCH", "/api/exams/e1/questions/q9")).toEqual({ points: 0.5 }));
    expect(sent(f, "POST", "/api/exams/e1/questions")).toEqual({ question_ids: ["q9"] });
    expect(f.mock.calls.some(([url, init]) => url === "/api/exams/e1/questions/q1" && (init as RequestInit)?.method === "DELETE")).toBe(true);
    // same place in the order, and the points the teacher had set, not the default of the type
    expect(sent(f, "PUT", "/api/exams/e1/order")).toEqual({ question_ids: ["q9", "q2", "q3"] });
    expect(screen.queryByTestId("swap-dialog")).not.toBeInTheDocument();
  });

  it("the automatic replacement is still one click", async () => {
    const f = mockFetch(
      route("POST", "/api/questions/search", searchPage([])),
      route("POST", "/api/exams/e1/questions/q1/swap", exam()),
      ...pageRoutes(exam({ subject_id: "s" })),
    );
    const u = userEvent.setup();
    renderWithQuery(<ExamDetailPage id="e1" />);
    await u.click(within(await screen.findByTestId("eq-1")).getByRole("button", { name: "Đổi câu" }));
    await u.click(await screen.findByRole("button", { name: "Để hệ thống chọn" }));
    await waitFor(() => expect(f.mock.calls.some(([url]) => url === "/api/exams/e1/questions/q1/swap")).toBe(true));
  });

  it("the questions table posts /exams/{id}/questions/search with its own filters", async () => {
    const f = mockFetch(route("POST", "/api/exams/e1/questions/search", searchPage([eq(1), eq(2, "II")])));
    setUrl("/org/exams?q.section=II&q.sort=-points");
    renderWithQuery(<ExamQuestionsTable examId="e1" />);
    expect(await screen.findByText("Câu 2")).toBeInTheDocument();
    expect(lastBody(f, "/exams/e1/questions/search")).toEqual({ page: 1, limit: 20, sort: [{ field: "points", desc: true }], filters: { section: { value: "II" } } });
  });
});
