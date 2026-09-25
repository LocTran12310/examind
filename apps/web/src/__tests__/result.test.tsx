import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AttemptResultPage } from "@/components/page-components/AttemptResult/AttemptResultPage";
import { ResultView } from "@/components/page-components/AttemptResult/ResultView/ResultView";
import { MeProvider } from "@/hooks/common/use-me";
import type { AttemptResult, AttemptView, ResultQuestion } from "@/interfaces/attempt.interface";
import { lastBody, me, mockFetch, renderWithQuery, route } from "./helpers";

const opts = ["A", "B", "C", "D"].map((l) => ({ label: l, content: `pa ${l}` }));
const rq = (o: Partial<ResultQuestion>): ResultQuestion => ({
  id: "q", type: "mcq", stem: "Đề", options: opts, answer: { key: "B" }, solution: "Lời giải", difficulty: null, grade: null, status: "approved",
  number: 1, part: null, confidence: 1, issues: [], parse_method: null, parse_model: null, answer_source: null, difficulty_source: null, subject_id: null, semester_code: null,
  exam_kind: null, topics: [], tags: [], section: "I", response: { key: "C" }, points: 0, max_points: 0.25, is_correct: false, comment: null, ...o,
});
const result = (o: Partial<AttemptResult> = {}): AttemptResult => ({
  id: "att", title: "Kiểm tra", status: "submitted", submitted_at: "", needs_grading: false, tab_switches: 2, hidden: false, score: 1.25, max_score: 2.5,
  score10: 5, sections: [{ section: "I", points: 0.25, max_points: 0.5 }], topics: [{ topic: "Vectơ", points: 0, max_points: 0.25, count: 1 }],
  questions: [rq({}), rq({ id: "q2", response: { key: "B" }, points: 0.25, is_correct: true })], ...o,
});
const essay = rq({ id: "e1", type: "essay", options: [], answer: { text: "mẫu" }, response: { text: "Bài làm" }, points: null, max_points: 1, is_correct: null });

afterEach(() => vi.unstubAllGlobals());

describe("result view", () => {
  it("shows score, breakdowns and per-question feedback", () => {
    renderWithQuery(<ResultView result={result()} />);
    expect(screen.getByTestId("score10")).toHaveTextContent("5");
    expect(screen.getAllByTestId("topic-row")[0]).toHaveTextContent("Vectơ");
    // still sorted so the topic to revise is on top, but the screen no longer names it (AC-04, ADR-02)
    expect(screen.getByText("Theo chuyên đề (tỉ lệ thấp trước)")).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent("yếu nhất");
    const first = screen.getByTestId("rq-1");
    expect(within(first).getByTestId("option-B")).toHaveAttribute("data-correct", "true");
    expect(within(first).getByTestId("option-C")).toHaveClass("bg-destructive/10");
    expect(within(first).getByTestId("solution")).toHaveTextContent("Lời giải");
    expect(screen.queryByText(/Rời tab/)).toBeNull();
  });

  it("hidden results explain the policy", () => {
    const { rerender } = renderWithQuery(<ResultView result={result({ hidden: true, reason: "never", questions: undefined })} />);
    expect(screen.getByRole("alert")).toHaveTextContent("chỉ cho xem điểm");
    expect(screen.getByText("5 điểm")).toBeInTheDocument();
    rerender(<ResultView result={result({ hidden: true, reason: "after_close", available_at: "2026-09-29T00:00:00Z", score10: undefined, questions: undefined })} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Đáp án và lời giải sẽ hiện sau khi đóng bài (29/09/2026 07:00).");
    expect(screen.queryByText(/điểm$/)).toBeNull();
  });

  it("teachers see whose attempt it is, tab switches, and grade essays (PATCH, then the result refetches)", async () => {
    const view = { id: "att", assignment_id: "a1", student: { id: "s", full_name: "Nguyễn An", username: "an" } } as AttemptView;
    const f = mockFetch(
      route("GET", "/api/attempts/att/result", result({ needs_grading: true, questions: [essay] })),
      route("GET", "/api/attempts/att", view),
      route("PATCH", "/api/attempts/att/answers/e1/grade", { score: 1.75, needs_grading: false }),
    );
    renderWithQuery(
      <MeProvider value={me("teacher")}>
        <AttemptResultPage id="att" />
      </MeProvider>,
    );
    expect(await screen.findByText("Bài làm của Nguyễn An (an)")).toBeInTheDocument();
    // the teacher came from the report of that bài giao (AC-07)
    expect(screen.getByRole("link", { name: "← Báo cáo bài giao" })).toHaveAttribute("href", "/org/assignments/a1");
    expect(screen.getByText("Rời tab 2 lần")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Điểm tự luận"), "0.5");
    await userEvent.type(screen.getByLabelText("Nhận xét"), "Thiếu bước 2");
    await userEvent.click(screen.getByRole("button", { name: "Lưu điểm" }));
    await waitFor(() => expect(f.mock.calls.filter(([url]) => url === "/api/attempts/att/result")).toHaveLength(2));
    const patch = f.mock.calls.find(([url]) => url === "/api/attempts/att/answers/e1/grade")!;
    expect((patch[1] as RequestInit).method).toBe("PATCH");
    expect(JSON.parse(String((patch[1] as RequestInit).body))).toEqual({ points: 0.5, comment: "Thiếu bước 2" });
    expect(() => lastBody(f, "/attempts/att/answers/e1/grade")).toThrow(); // not a POST
  });

  it("a student neither loads the attempt nor sees the grader", async () => {
    const f = mockFetch(route("GET", "/api/attempts/att/result", result({ questions: [essay] })));
    renderWithQuery(
      <MeProvider value={me("student")}>
        <AttemptResultPage id="att" />
      </MeProvider>,
    );
    expect(await screen.findByTestId("rq-1")).toBeInTheDocument();
    expect(screen.queryByTestId("essay-grader")).toBeNull();
    expect(f.mock.calls.some(([url]) => url === "/api/attempts/att")).toBe(false);
    // a student goes back to their own list of assignments (AC-07)
    expect(screen.getByRole("link", { name: "← Bài được giao" })).toHaveAttribute("href", "/home");
  });

  it("a failed load shows the error", async () => {
    mockFetch(route("GET", "/api/attempts/att/result", { code: "not_found", message: "Không tìm thấy bài làm" }, 404));
    renderWithQuery(
      <MeProvider value={me("student")}>
        <AttemptResultPage id="att" />
      </MeProvider>,
    );
    expect(await screen.findByText("Không tìm thấy bài làm")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "← Bài được giao" })).toHaveAttribute("href", "/home");
  });
});
