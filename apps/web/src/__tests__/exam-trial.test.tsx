import { act, fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ResultView } from "@/components/page-components/AttemptResult/ResultView/ResultView";
import { AssignedList } from "@/components/page-components/ExamDetail/AssignedList/AssignedList";
import { ExamTrialPage } from "@/components/page-components/ExamTrial/ExamTrialPage";
import type { Assignment, AssignmentPaper } from "@/interfaces/assignment.interface";
import type { AttemptQuestion, AttemptResult, ResultQuestion } from "@/interfaces/attempt.interface";
import { lastBody, mockFetch, renderWithQuery, route } from "./helpers";

const opts = ["A", "B", "C", "D"].map((l) => ({ label: l, content: `pa ${l}` }));
const q = (n: number, o: Partial<AttemptQuestion> = {}): AttemptQuestion => ({
  id: `q${n}`, type: "mcq", stem: `Câu hỏi số ${n}`, options: opts, answer: null, solution: "", difficulty: null, grade: null, status: "approved",
  number: n, section: "I", points: 0.25, response: null, ...o,
});
/** `GET /assignments/{id}/paper`: no attempt id, no deadline, no server clock — nobody is sitting it. */
const paper = (): AssignmentPaper => ({
  assignment_id: "a1", exam_id: "e1", title: "Kiểm tra giữa kỳ", max_score: 0.75,
  questions: [q(1), q(2), q(3, { type: "short_answer", options: [] })],
});
const assignment = (o: Partial<Assignment> = {}): Assignment => ({
  id: "a1", exam_id: "e1", title: "Kiểm tra giữa kỳ", open_at: "2026-09-24T01:00:00Z", close_at: "2026-09-24T03:00:00Z", duration_minutes: 45,
  max_attempts: 1, shuffle_questions: false, shuffle_options: false, results_policy: "after_submit", students: 30, submitted: 0, classes: ["10A"], ...o,
});
const rq = (o: Partial<ResultQuestion>): ResultQuestion => ({
  id: "q1", type: "mcq", stem: "Câu hỏi số 1", options: opts, answer: { key: "B" }, solution: "Lời giải", difficulty: null, grade: null, status: "approved",
  number: 1, part: null, confidence: 1, issues: [], parse_method: null, parse_model: null, answer_source: null, subject_id: null, semester_code: null,
  exam_kind: null, topics: [], tags: [], section: "I", response: { key: "B" }, points: 0.25, max_points: 0.25, is_correct: true, comment: null, ...o,
});
const essay = rq({ id: "e1", type: "essay", options: [], answer: { text: "mẫu" }, response: { text: "Bài làm thử" }, points: null, max_points: 1, is_correct: null });
/** `POST /assignments/{id}/trial`: an attempt's result shape with `id: null` — there is no attempt (ADR-01). */
const graded = (o: Partial<AttemptResult> = {}): AttemptResult => ({
  id: null, title: "Kiểm tra giữa kỳ", status: "submitted", submitted_at: "2026-09-24T02:00:00Z", needs_grading: false, tab_switches: 0, hidden: false,
  score: 0.25, max_score: 0.75, score10: 3.33, sections: [{ section: "I", points: 0.25, max_points: 0.75 }],
  topics: [{ topic: "Vectơ", points: 0.25, max_points: 0.25, count: 1 }], questions: [rq({})], ...o,
});

describe("exam trial", () => {
  beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }));
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("the way in is the assigned list of the exam, beside the report (AC-04)", () => {
    renderWithQuery(<AssignedList assigned={[assignment()]} />);
    expect(screen.getByRole("link", { name: "Làm thử" })).toHaveAttribute("href", "/org/assignments/a1/trial");
    // the report is still what the title points at
    expect(screen.getByRole("link", { name: "Kiểm tra giữa kỳ" })).toHaveAttribute("href", "/org/assignments/a1");
  });

  it("runs the student's screen with no clock, no autosave and no tab report (AC-04)", async () => {
    const f = mockFetch(route("GET", "/api/assignments/a1/paper", paper()));
    renderWithQuery(<ExamTrialPage id="a1" />);
    expect(await screen.findByTestId("exam-question")).toHaveTextContent("Câu hỏi số 1");
    expect(screen.getByText("Chạy thử · không ghi lại gì")).toBeInTheDocument();
    expect(screen.getByText(/không một lượt làm bài, điểm hay thống kê nào được ghi lại/)).toBeInTheDocument();
    expect(screen.queryByTestId("timer")).toBeNull();
    expect(screen.queryByText("Đã lưu")).toBeNull();
    // the answer is held on the screen, and nothing is sent: there is no attempt to save it to (ADR-01)
    fireEvent.click(screen.getByTestId("option-B"));
    await act(async () => void vi.advanceTimersByTime(5000));
    expect(screen.getByTestId("option-B")).toHaveClass("bg-primary/10");
    // nobody invigilates a rehearsal either
    Object.defineProperty(document, "visibilityState", { value: "hidden", configurable: true });
    document.dispatchEvent(new Event("visibilitychange"));
    Object.defineProperty(document, "visibilityState", { value: "visible", configurable: true });
    await act(async () => void vi.advanceTimersByTime(5000));
    expect(f.mock.calls.map((c) => c[0])).toEqual(["/api/assignments/a1/paper"]);
  });

  it("the whole-paper mode and the navigator are the student's, unchanged (AC-04)", async () => {
    mockFetch(route("GET", "/api/assignments/a1/paper", paper()));
    renderWithQuery(<ExamTrialPage id="a1" />);
    await screen.findByTestId("exam-question");
    fireEvent.click(screen.getByRole("radio", { name: "Toàn đề" }));
    expect(screen.getAllByTestId("exam-question")).toHaveLength(3);
    expect(screen.getByText(/còn 3 câu chưa làm/)).toBeInTheDocument();
    fireEvent.click(within(screen.getAllByTestId("exam-question")[1]).getByTestId("option-A"));
    expect(screen.getByText(/còn 2 câu chưa làm/)).toBeInTheDocument();
    expect(within(screen.getByTestId("navigator")).getByRole("button", { name: "Câu 2" })).toHaveAttribute("aria-current", "true");
    fireEvent.click(screen.getByRole("radio", { name: "Một câu" }));
    expect(screen.getByTestId("exam-question")).toHaveTextContent("Câu hỏi số 2");
  });

  it("grades in one call and shows the student's own result screen (AC-05)", async () => {
    const f = mockFetch(route("GET", "/api/assignments/a1/paper", paper()), route("POST", "/api/assignments/a1/trial", graded()));
    renderWithQuery(<ExamTrialPage id="a1" />);
    await screen.findByTestId("exam-question");
    fireEvent.click(screen.getByTestId("option-B"));
    fireEvent.click(screen.getByRole("button", { name: "Chấm thử" }));
    expect(screen.getByText(/Bản chạy thử được chấm ngay và không ghi lại gì/)).toBeInTheDocument();
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Chấm thử" }));
    expect(await screen.findByTestId("score10")).toHaveTextContent("3.33");
    // the answers of every question go in one body, the unanswered ones as null
    expect(lastBody(f, "/assignments/a1/trial")).toEqual({ responses: { q1: { key: "B" }, q2: null, q3: null } });
    expect(screen.getByTestId("rq-1")).toBeInTheDocument();
    expect(screen.getAllByTestId("topic-row")[0]).toHaveTextContent("Vectơ");
    expect(screen.getByText(/Không có lượt làm bài, điểm hay thống kê nào được ghi lại/)).toBeInTheDocument();
    // reading the paper and grading it are the only two calls the whole trial makes
    expect(f.mock.calls.map((c) => c[0])).toEqual(["/api/assignments/a1/paper", "/api/assignments/a1/trial"]);
  });

  it("a trial result has no essay grader: there is no attempt to grade against (AC-05)", () => {
    renderWithQuery(<ResultView result={graded({ needs_grading: true, questions: [essay] })} staff />);
    expect(screen.getByTestId("rq-1")).toHaveTextContent("Bài làm thử");
    expect(screen.queryByTestId("essay-grader")).toBeNull();
  });

  it("a paper that cannot be read says so, and the way back stays", async () => {
    mockFetch(route("GET", "/api/assignments/a1/paper", { code: "not_found", message: "Không tìm thấy bài giao" }, 404));
    renderWithQuery(<ExamTrialPage id="a1" />);
    expect(await screen.findByText("Không tìm thấy bài giao")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "← Đề thi" })).toHaveAttribute("href", "/org/exams");
    expect(screen.queryByTestId("exam-question")).toBeNull();
  });
});
