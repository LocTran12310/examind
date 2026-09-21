import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ResultView } from "@/components/exams/ResultView";
import type { AttemptResult, ResultQuestion } from "@/lib/types";
import { mockFetch, route } from "./helpers";

const opts = ["A", "B", "C", "D"].map((l) => ({ label: l, content: `pa ${l}` }));
const rq = (o: Partial<ResultQuestion>): ResultQuestion => ({
  id: "q", type: "mcq", stem: "Đề", options: opts, answer: { key: "B" }, solution: "Lời giải", difficulty: null, grade: null, status: "approved",
  number: 1, part: null, confidence: 1, issues: [], parse_method: null, parse_model: null, answer_source: null, subject_id: null, semester_code: null,
  exam_kind: null, topics: [], tags: [], section: "I", response: { key: "C" }, points: 0, max_points: 0.25, is_correct: false, comment: null, ...o,
});
const result = (o: Partial<AttemptResult> = {}): AttemptResult => ({
  id: "att", title: "Kiểm tra", status: "submitted", submitted_at: "", needs_grading: false, tab_switches: 2, hidden: false, score: 1.25, max_score: 2.5,
  score10: 5, sections: [{ section: "I", points: 0.25, max_points: 0.5 }], topics: [{ topic: "Vectơ", points: 0, max_points: 0.25, count: 1 }],
  questions: [rq({}), rq({ id: "q2", response: { key: "B" }, points: 0.25, is_correct: true })], ...o,
});

afterEach(() => vi.unstubAllGlobals());

describe("result view", () => {
  it("shows score, breakdowns and per-question feedback", () => {
    render(<ResultView result={result()} />);
    expect(screen.getByTestId("score10")).toHaveTextContent("5");
    expect(screen.getAllByTestId("topic-row")[0]).toHaveTextContent("Vectơ");
    const first = screen.getByTestId("rq-1");
    expect(within(first).getByTestId("option-B")).toHaveAttribute("data-correct", "true");
    expect(within(first).getByTestId("option-C")).toHaveClass("bg-red-50");
    expect(within(first).getByTestId("solution")).toHaveTextContent("Lời giải");
    expect(screen.queryByText(/Rời tab/)).toBeNull();
  });

  it("hidden results explain the policy", () => {
    render(<ResultView result={result({ hidden: true, reason: "never", questions: undefined })} />);
    expect(screen.getByRole("alert")).toHaveTextContent("chỉ cho xem điểm");
  });

  it("teachers grade essays and see tab switches", async () => {
    const f = mockFetch(route("PATCH", "/api/attempts/att/answers/e1/grade", { score: 1.75, needs_grading: false }));
    const onChange = vi.fn();
    const essay = rq({ id: "e1", type: "essay", options: [], answer: { text: "mẫu" }, response: { text: "Bài làm" }, points: null, max_points: 1, is_correct: null });
    render(<ResultView result={result({ needs_grading: true, questions: [essay] })} staff onChange={onChange} />);
    expect(screen.getByText("Rời tab 2 lần")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Điểm tự luận"), "0.5");
    await userEvent.type(screen.getByLabelText("Nhận xét"), "Thiếu bước 2");
    await userEvent.click(screen.getByRole("button", { name: "Lưu điểm" }));
    await waitFor(() => expect(onChange).toHaveBeenCalled());
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ points: 0.5, comment: "Thiếu bước 2" });
  });
});
