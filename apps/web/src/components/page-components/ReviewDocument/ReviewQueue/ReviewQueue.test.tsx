import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { mockFetch, renderWithQuery as render, route } from "@/__tests__/helpers";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { ReviewQueue } from "./ReviewQueue";

const opts = ["A", "B", "C", "D"].map((l) => ({ label: l, content: l.toLowerCase() }));
const pq = (id: string, n: number, o: Partial<ParsedQuestion> = {}): ParsedQuestion => ({
  id, type: "mcq", stem: `Câu hỏi ${n}`, options: opts, answer: null, solution: "", difficulty: null, grade: 10, status: "needs_review",
  number: n, part: null, confidence: 0.8, issues: ["thiếu đáp án"], parse_method: "rule", parse_model: null, answer_source: null,
  subject_id: null, semester_code: null, exam_kind: null, topics: [], tags: [], page: 1, group: "thiếu đáp án", ...o,
});
const topics: Topic[] = [
  { id: "t1", subject_id: "s", parent_id: null, name: "Giải tích", level_kind: "strand", grade: null, path: "a", depth: 1, sort: 0, child_count: 1 },
  { id: "t2", subject_id: "s", parent_id: "t1", name: "Nguyên hàm", level_kind: "topic", grade: 12, path: "a.b", depth: 2, sort: 0, child_count: 0 },
];
const press = (key: string) => act(() => void fireEvent.keyDown(window, { key }));

afterEach(() => vi.unstubAllGlobals());

describe("review queue", () => {
  it("2 sets the answer, Enter approves and moves on", async () => {
    const f = mockFetch(
      (url, init) => (url === "/api/questions/q1" && init?.method === "PATCH" ? { body: pq("q1", 1, { answer: { key: "B" }, issues: [] }) } : undefined),
      route("POST", "/api/review/questions/q1/action", pq("q1", 1, { status: "approved", answer: { key: "B" }, issues: [] })),
    );
    render(<ReviewQueue doc={{ id: "d", mime: "application/pdf" }} initial={[pq("q1", 1), pq("q2", 2)]} topics={topics} />);
    expect(screen.getByTestId("counter")).toHaveTextContent("1/2");
    expect(screen.getByTestId("source-page").querySelector("img")).toHaveAttribute("src", "/api/documents/d/pages/1.png");
    press("2");
    await waitFor(() => expect(screen.getByTestId("option-B")).toHaveAttribute("data-correct", "true"));
    press("Enter");
    await waitFor(() => expect(screen.getByTestId("counter")).toHaveTextContent("2/2"));
    const calls = f.mock.calls.map((c) => [c[0], c[1]?.method, c[1]?.body]);
    expect(calls[0]).toEqual(["/api/questions/q1", "PATCH", JSON.stringify({ answer: { key: "B" } })]);
    expect(calls[1]).toEqual(["/api/review/questions/q1/action", "POST", JSON.stringify({ action: "approve" })]);
  });

  it("blocking issues are reported and the question stays", async () => {
    mockFetch(route("POST", "/api/review/questions/q1/action", { code: "has_blocking_issues", message: "Câu còn lỗi: thiếu đáp án" }, 409));
    render(<ReviewQueue doc={{ id: "d", mime: "application/vnd" }} initial={[pq("q1", 1), pq("q2", 2)]} topics={topics} />);
    expect(screen.queryByTestId("source-page")).toBeNull();
    press("Enter");
    expect(await screen.findByRole("alert")).toHaveTextContent("Câu còn lỗi: thiếu đáp án");
    expect(screen.getByTestId("counter")).toHaveTextContent("1/2");
  });

  it("X rejects, J/K navigate, T picks a topic by keyboard", async () => {
    const f = mockFetch(
      route("POST", "/api/review/questions/q1/action", pq("q1", 1, { status: "rejected" })),
      (url, init) => (url === "/api/questions/q2" && init?.method === "PATCH"
        ? { body: pq("q2", 2, { topics: [{ id: "t2", name: "Nguyên hàm", is_primary: true, source: "manual", score: 1 }] }) } : undefined),
    );
    render(<ReviewQueue doc={{ id: "d", mime: "x" }} initial={[pq("q1", 1), pq("q2", 2)]} topics={topics} />);
    press("x");
    await waitFor(() => expect(screen.getByTestId("counter")).toHaveTextContent("2/2"));
    press("k");
    expect(screen.getByTestId("counter")).toHaveTextContent("1/2");
    press("j");
    press("t");
    const input = await screen.findByPlaceholderText(/Tìm chuyên đề/);
    fireEvent.change(input, { target: { value: "nguyen ham" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("topic-button")).toHaveTextContent("Nguyên hàm"));
    expect(JSON.parse(String(f.mock.calls.at(-1)?.[1]?.body))).toEqual({ primary_topic_id: "t2" });
  });

  it("true/false keys toggle statements", async () => {
    const tf = pq("q3", 3, { type: "true_false", options: ["a", "b", "c", "d"].map((l) => ({ label: l, content: l, is_true: null })), answer: null });
    const f = mockFetch((url, init) => (init?.method === "PATCH" ? { body: tf } : undefined));
    render(<ReviewQueue doc={{ id: "d", mime: "x" }} initial={[tf]} topics={topics} />);
    press("2");
    await waitFor(() => expect(f).toHaveBeenCalled());
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ answer: { a: false, b: true, c: false, d: false } });
  });
});
