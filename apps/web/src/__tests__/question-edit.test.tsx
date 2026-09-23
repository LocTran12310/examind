import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { formValueOf, payloadOf, QuestionForm } from "@/components/common/QuestionForm/QuestionForm";
import { QuestionDetailPage } from "@/components/page-components/QuestionDetail/QuestionDetailPage";
import { QuestionNewPage } from "@/components/page-components/QuestionNew/QuestionNewPage";
import { QuestionPreviewPage } from "@/components/page-components/QuestionPreview/QuestionPreviewPage";
import type { ParsedQuestion, QuestionStats } from "@/interfaces/question.interface";
import type { Tag } from "@/interfaces/tag.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const taxonomy: Taxonomy = { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [{ id: "g", level: 10, name: "Lớp 10" }], semesters: [] };
const topics: Topic[] = [{ id: "t1", subject_id: "s", parent_id: null, name: "Vectơ", level_kind: "topic", grade: 10, path: "a", depth: 1, sort: 0, child_count: 0 }];
const tags: Tag[] = [{ id: "g1", group: "method", name: "đổi biến" }];
const thin: QuestionStats = { observations: 4, enough_data: false, correct_ratio: null, first_attempt_ratio: null,
  discrimination: null, median_seconds: null, options: [] };
const demo = { id: "demo", type: "mcq", stem: "Câu mẫu", options: "ABCD".split("").map((l) => ({ label: l, content: l })), answer: { key: "A" },
  solution: "", difficulty: null, grade: null, status: "approved", subject_id: null, topics: [], tags: [] } as unknown as ParsedQuestion;

describe("question form", () => {
  it("creates a new MCQ with topic, tag, difficulty and a preview", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<QuestionForm initial={formValueOf()} taxonomy={taxonomy} topics={topics} tags={tags} submitLabel="Tạo câu hỏi" onSubmit={onSubmit} />);
    fireEvent.change(screen.getByTestId("stem"), { target: { value: "Cho $\\vec u = (1;2)$. Độ dài bằng" } });
    for (const [i, v] of ["$\\sqrt5$", "3", "5", "1"].entries()) fireEvent.change(screen.getByLabelText(`Phương án ${"ABCD"[i]}`), { target: { value: v } });
    await userEvent.click(screen.getAllByRole("radio")[0]);
    await userEvent.click(screen.getByRole("combobox", { name: "Mức độ" }));
    await userEvent.click(await screen.findByRole("option", { name: "Thông hiểu" }));
    expect(screen.getByRole("combobox", { name: "Mức độ" })).toHaveTextContent("Thông hiểu");
    await userEvent.click(screen.getByTestId("pick-topic"));
    await userEvent.click(within(screen.getByRole("tree", { name: "Cây chuyên đề" })).getByText("Vectơ"));
    await userEvent.click(within(screen.getByTestId("tag-options")).getByRole("checkbox"));
    expect(screen.getByTestId("preview").querySelector(".katex")).not.toBeNull();
    await userEvent.click(screen.getByText(/Tạo câu hỏi/)); // role+name queries trip jsdom on KaTeX markup
    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    const body = payloadOf(onSubmit.mock.calls[0][0]);
    expect(body).toMatchObject({ type: "mcq", answer: { key: "A" }, difficulty: "th", primary_topic_id: "t1", tag_ids: ["g1"], subject_id: null });
  });

  it("edit form is prefilled from the question", () => {
    const q = { id: "q", type: "mcq", stem: "Đề cũ", options: "ABCD".split("").map((l) => ({ label: l, content: l })), answer: { key: "D" },
      solution: "Giải", difficulty: "vd", grade: 10, subject_id: "s", topics: [{ id: "t1", name: "Vectơ", is_primary: true, source: "manual", score: 1 }],
      tags: [{ id: "g1", group: "method", name: "đổi biến" }] } as unknown as ParsedQuestion;
    render(<QuestionForm initial={formValueOf(q)} taxonomy={taxonomy} topics={topics} tags={tags} submitLabel="Lưu" onSubmit={vi.fn()} />);
    expect(screen.getByTestId("stem")).toHaveValue("Đề cũ");
    expect(screen.getAllByRole("radio")[3]).toBeChecked();
    expect(screen.getByTestId("pick-topic")).toHaveTextContent("Vectơ");
    expect(within(screen.getByTestId("tag-options")).getByRole("checkbox")).toBeChecked();
  });
});

describe("save shortcut (ui-polish AC-05)", () => {
  it("⌘+Enter saves, also while a Vietnamese IME composes (key 'Process')", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<QuestionForm initial={formValueOf()} taxonomy={taxonomy} topics={topics} tags={tags} submitLabel="Lưu" onSubmit={onSubmit} />);
    fireEvent.keyDown(screen.getByTestId("stem"), { key: "Process", code: "Enter", metaKey: true, keyCode: 229 });
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    fireEvent.keyDown(document.body, { key: "Enter", code: "Enter", ctrlKey: true });
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(2));
  });

  it("the topic picker is a tree: search keeps ancestors, Enter picks the match", async () => {
    const tree: Topic[] = [
      { id: "gt", subject_id: "s", parent_id: null, name: "Giải tích", level_kind: "strand", grade: null, path: "a", depth: 1, sort: 0, child_count: 1 },
      { id: "nh", subject_id: "s", parent_id: "gt", name: "Nguyên hàm", level_kind: "topic", grade: 12, path: "a.b", depth: 2, sort: 0, child_count: 0 },
    ];
    const u = userEvent.setup();
    render(<QuestionForm initial={formValueOf()} taxonomy={taxonomy} topics={tree} tags={tags} submitLabel="Lưu" onSubmit={vi.fn()} />);
    await u.click(screen.getByTestId("pick-topic"));
    const t = screen.getByRole("tree", { name: "Cây chuyên đề" });
    // no number beside a topic here: this picker has no subject facets to count questions with (AC-02)
    expect(within(t).getAllByRole("treeitem").map((x) => x.textContent)).toEqual(["Giải tích"]); // collapsed
    await u.type(screen.getByLabelText("Tìm chuyên đề"), "nguyen");
    expect(within(t).getAllByRole("treeitem").map((x) => x.textContent)).toEqual(["Giải tích", "Nguyên hàm"]);
    await u.keyboard("{Enter}");
    expect(screen.getByTestId("pick-topic")).toHaveTextContent("Giải tích › Nguyên hàm");
  });
});

describe("question detail page", () => {
  it("edits the question: PATCH with the whole form, then shows the saved version", async () => {
    const q = { id: "q", number: 3, type: "mcq", stem: "Đề cũ", options: "ABCD".split("").map((l) => ({ label: l, content: l })), answer: { key: "D" },
      solution: "", difficulty: "vd", grade: 10, status: "approved", subject_id: "s", topics: [{ id: "t1", name: "Vectơ", is_primary: true, source: "manual", score: 1 }],
      tags: [] } as unknown as ParsedQuestion;
    let saved = q;
    const fetch = mockFetch(
      (url, init) => (url === "/api/questions/q" && init?.method === "GET" ? { body: saved } : undefined),
      (url, init) => (url === "/api/questions/q" && init?.method === "PATCH" ? { body: (saved = { ...q, stem: "Đề mới" }) } : undefined),
      route("GET", "/api/questions/q/stats", thin),
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", "/api/topics?subject_id=s", topics),
      route("POST", "/api/tags/search", searchPage(tags)),
    );
    const u = userEvent.setup();
    render(<QuestionDetailPage id="q" />);
    await u.click(await screen.findByRole("button", { name: "Sửa" }));
    fireEvent.change(screen.getByTestId("stem"), { target: { value: "Đề mới" } });
    await u.click(screen.getByText(/^Lưu/));
    await waitFor(() => expect(screen.queryByTestId("stem")).toBeNull());
    const call = fetch.mock.calls.find(([url, init]) => url === "/api/questions/q" && (init as RequestInit | undefined)?.method === "PATCH");
    expect(JSON.parse(String((call?.[1] as RequestInit).body))).toMatchObject({ stem: "Đề mới", answer: { key: "D" }, subject_id: "s", primary_topic_id: "t1", topic_ids: ["t1"] });
    expect(await screen.findByText("Đề mới")).toBeInTheDocument();
  });
});

describe("question statistics (learning-telemetry AC-03)", () => {
  const q = { id: "q", number: 3, type: "mcq", stem: "Đề", options: "ABCD".split("").map((l) => ({ label: l, content: l })),
    answer: { key: "B" }, solution: "", difficulty: "vd", grade: 10, status: "approved", subject_id: "s",
    topics: [{ id: "t1", name: "Vectơ", is_primary: true, source: "manual", score: 1 }], tags: [] } as unknown as ParsedQuestion;

  const detail = (stats: QuestionStats) =>
    mockFetch(
      route("GET", "/api/questions/q/stats", stats),
      route("GET", "/api/questions/q", q),
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", "/api/topics?subject_id=s", topics),
      route("POST", "/api/tags/search", searchPage(tags)),
    );

  it("shows the numbers with their observation count and the option distribution, key marked", async () => {
    detail({ observations: 12, enough_data: true, correct_ratio: 0.667, first_attempt_ratio: 0.5, discrimination: 0.4,
      median_seconds: 75, options: [{ label: "A", chosen: 4, ratio: 0.333, is_key: false }, { label: "B", chosen: 8, ratio: 0.667, is_key: true }] });
    render(<QuestionDetailPage id="q" />);
    const panel = await screen.findByTestId("question-stats");
    expect(panel).toHaveTextContent("Tỉ lệ đúng");
    expect(panel).toHaveTextContent("67%");
    expect(panel).toHaveTextContent("Đúng ngay lần đầu");
    expect(panel).toHaveTextContent("50%");
    expect(panel).toHaveTextContent("+0.40");
    expect(panel).toHaveTextContent("1 phút 15 giây");
    expect(within(panel).getAllByText(/lượt/).map((e) => e.textContent)).toContain("12 lượt");
    const options = within(panel).getByTestId("option-stats");
    expect(within(options).getAllByRole("listitem").map((li) => li.textContent)).toEqual(["A33%4 lượt", "B✓ đáp án67%8 lượt"]);
  });

  it("says chưa đủ dữ liệu below ten answers and shows no number", async () => {
    detail(thin);
    render(<QuestionDetailPage id="q" />);
    const panel = await screen.findByTestId("question-stats");
    expect(panel).toHaveTextContent("Chưa đủ dữ liệu — cần ít nhất 10 lượt trả lời (hiện có 4).");
    expect(within(panel).queryByTestId("option-stats")).toBeNull();
    expect(panel).not.toHaveTextContent("Tỉ lệ đúng");
  });
});

describe("the way back to the bank (AC-07)", () => {
  it("the new-question form links to the question bank", async () => {
    mockFetch(route("GET", "/api/taxonomy", taxonomy), route("GET", "/api/topics", topics), route("POST", "/api/tags/search", searchPage(tags)));
    render(<QuestionNewPage />);
    expect(await screen.findByRole("link", { name: "← Ngân hàng câu hỏi" })).toHaveAttribute("href", "/org/bank");
  });

  it("the question preview links to the question bank", async () => {
    mockFetch(route("GET", "/api/questions/demo", demo));
    render(<QuestionPreviewPage />);
    expect(await screen.findByRole("link", { name: "← Ngân hàng câu hỏi" })).toHaveAttribute("href", "/org/bank");
  });
});
