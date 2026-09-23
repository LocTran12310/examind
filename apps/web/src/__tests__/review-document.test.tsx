import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReviewDocumentPage } from "@/components/page-components/ReviewDocument/ReviewDocumentPage";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { ReviewDocument } from "@/interfaces/review.interface";
import type { Tag } from "@/interfaces/tag.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { lastBody, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const opts = ["A", "B", "C", "D"].map((l) => ({ label: l, content: l.toLowerCase() }));
const pq = (id: string, n: number, o: Partial<ParsedQuestion> = {}): ParsedQuestion => ({
  id, type: "mcq", stem: `Câu hỏi ${n}`, options: opts, answer: { key: "A" }, solution: "", difficulty: null, grade: 10, status: "needs_review",
  number: n, part: null, confidence: 0.8, issues: [], parse_method: "rule", parse_model: null, answer_source: null,
  subject_id: "s", semester_code: null, exam_kind: null, topics: [], tags: [], page: 1, group: "thiếu đáp án", ...o,
});
const doc: ReviewDocument = {
  document: { id: "d1", filename: "15. CHUYÊN ĐHKHTN.docx", mime: "application/vnd", meta: { subject_id: "s" } } as ReviewDocument["document"],
  total: 22,
  counts: { auto_approved: 11, needs_review: 11, approved: 0, rejected: 0, duplicate: 0, flagged: 0 },
  spot_pending: 1, progress: 0.5, review_state: "pending", pending: 12, assigned_to: null, assigned_name: null,
};
const taxonomy: Taxonomy = { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [{ id: "g", level: 10, name: "Lớp 10" }], semesters: [] };
const topics: Topic[] = [{ id: "t1", subject_id: "s", parent_id: null, name: "Vectơ", level_kind: "topic", grade: 10, path: "a", depth: 1, sort: 0, child_count: 0 }];
const tags: Tag[] = [{ id: "g1", group: "method", name: "đổi biến" }];
const approved = pq("q9", 9, { status: "approved", stem: "Câu đã duyệt", group: null });

/** The document, its queue and everything the editor needs; the caller adds what its case asserts. */
const base = () => [
  route("GET", "/api/review/documents/d1", doc),
  route("GET", "/api/review/documents/d1/queue", [pq("q1", 1), pq("q2", 2)]),
  route("GET", /\/api\/topics/, topics),
  route("GET", "/api/taxonomy", taxonomy),
  route("POST", "/api/tags/search", searchPage(tags)),
  route("POST", "/api/review/documents/d1/questions/search", searchPage([approved])),
];

beforeEach(() => setUrl("/org/review/d1"));

describe("review document", () => {
  it("the state filter reaches the body and lists what was decided", async () => {
    const fetch = mockFetch(...base());
    const u = userEvent.setup();
    render(<ReviewDocumentPage id="d1" />);
    await screen.findByTestId("queue-card"); // "Cần xem" is the keyboard queue
    await u.click(screen.getByRole("radio", { name: "Đã duyệt" }));
    const row = await screen.findByTestId("question-q9");
    expect(lastBody(fetch, "/review/documents/d1/questions/search")).toMatchObject({ state: "approved", page: 1 });
    expect(row).toHaveTextContent("Câu 9");
    expect(row).toHaveTextContent("Đã duyệt"); // the row names its own state (AC-05)
    expect(screen.queryByTestId("queue-card")).toBeNull();
  });

  it("an approved question opens in the full form and is corrected", async () => {
    const fetch = mockFetch(...base(), route("PATCH", "/api/questions/q9", { ...approved, stem: "Câu đã sửa" }));
    const u = userEvent.setup();
    render(<ReviewDocumentPage id="d1" />);
    await screen.findByTestId("queue-card");
    await u.click(screen.getByRole("radio", { name: "Đã duyệt" }));
    await u.click(await screen.findByRole("button", { name: "Sửa nội dung câu hỏi" }));
    fireEvent.change(screen.getByTestId("stem"), { target: { value: "Câu đã sửa" } });
    await u.click(screen.getByText(/Lưu câu hỏi/));
    await waitFor(() => {
      const call = fetch.mock.calls.find(([url, init]) => url === "/api/questions/q9" && (init as RequestInit)?.method === "PATCH");
      expect(JSON.parse(String((call?.[1] as RequestInit).body))).toMatchObject({ stem: "Câu đã sửa", type: "mcq" });
    });
  });

  it("a re-decision sends the status the button announced and refetches the document", async () => {
    const fetch = mockFetch(...base(), route("POST", "/api/questions/bulk", { updated: 1 }));
    const u = userEvent.setup();
    render(<ReviewDocumentPage id="d1" />);
    await screen.findByTestId("queue-card");
    await u.click(screen.getByRole("radio", { name: "Đã duyệt" }));
    await screen.findByTestId("question-q9");
    const before = fetch.mock.calls.filter(([url]) => url === "/api/review/documents/d1/questions/search").length;
    await u.click(screen.getByRole("button", { name: "Trả lại — chuyển sang Cần xem" }));
    await waitFor(() => expect(lastBody(fetch, "/questions/bulk")).toEqual({ ids: ["q9"], set: { status: "needs_review" } }));
    // the counts of the document and its questions follow
    await waitFor(() => expect(fetch.mock.calls.filter(([url]) => url === "/api/review/documents/d1/questions/search").length).toBeGreaterThan(before));
    await waitFor(() => expect(fetch.mock.calls.filter(([url, init]) => url === "/api/review/documents/d1" && (init as RequestInit).method === "GET").length).toBeGreaterThan(1));
  });

  it("the keyboard flow of the pending queue is untouched", async () => {
    const fetch = mockFetch(...base(), route("POST", "/api/review/questions/q1/action", pq("q1", 1, { status: "approved" })));
    render(<ReviewDocumentPage id="d1" />);
    await screen.findByTestId("queue-card");
    expect(screen.getByTestId("counter")).toHaveTextContent("1/2");
    act(() => void fireEvent.keyDown(window, { key: "Enter" }));
    await waitFor(() => expect(screen.getByTestId("counter")).toHaveTextContent("2/2"));
    expect(lastBody(fetch, "/review/questions/q1/action")).toEqual({ action: "approve" });
  });
});
