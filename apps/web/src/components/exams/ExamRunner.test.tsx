import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mockFetch } from "@/__tests__/helpers";
import type { AttemptQuestion, AttemptView } from "@/lib/types";
import { ExamRunner, formatLeft } from "./ExamRunner";

const opts = ["A", "B", "C", "D"].map((l) => ({ label: l, content: `pa ${l}` }));
const q = (n: number, o: Partial<AttemptQuestion> = {}): AttemptQuestion => ({
  id: `q${n}`, type: "mcq", stem: `Câu hỏi số ${n}`, options: opts, answer: null, solution: "", difficulty: null, grade: null, status: "approved",
  number: n, section: "I", points: 0.25, response: null, ...o,
});
const view = (deadlineInMs = 600_000, o: Partial<AttemptView> = {}): AttemptView => ({
  id: "att", title: "Kiểm tra", status: "in_progress", started_at: new Date().toISOString(),
  deadline_at: new Date(Date.now() + deadlineInMs).toISOString(), submitted_at: null, server_now: new Date().toISOString(), tab_switches: 0,
  student: { id: "s", full_name: "HS", username: "hs" }, assignment_id: "a",
  questions: [q(1, { response: { key: "C" } }), q(2), q(3, { type: "true_false", options: ["a", "b", "c", "d"].map((l) => ({ label: l, content: l })) }),
    q(4, { type: "short_answer", options: [] })], ...o,
});

describe("exam runner", () => {
  beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }));
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("formats time", () => {
    expect(formatLeft(65_000)).toBe("01:05");
    expect(formatLeft(3_725_000)).toBe("1:02:05");
    expect(formatLeft(-5)).toBe("00:00");
  });

  it("restores answers, autosaves after a debounce and shows the unsaved badge", async () => {
    const f = mockFetch((url, init) => (init?.method === "PUT" ? { body: { ok: true } } : undefined));
    render(<ExamRunner view={view()} onFinished={() => {}} />);
    expect(screen.getByTestId("option-C")).toHaveClass("bg-brand-50");
    fireEvent.click(within(screen.getByTestId("navigator")).getByRole("button", { name: "Câu 2" }));
    fireEvent.click(screen.getByTestId("option-B"));
    expect(screen.getByText("Chưa lưu 1")).toBeInTheDocument();
    await act(async () => void vi.advanceTimersByTime(600));
    await waitFor(() => expect(screen.getByText("Đã lưu")).toBeInTheDocument());
    expect(f.mock.calls[0][0]).toBe("/api/attempts/att/answers/q2");
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ response: { key: "B" } });
  });

  it("true/false and short answer inputs; counts unanswered", async () => {
    mockFetch((url, init) => (init?.method === "PUT" ? { body: {} } : undefined));
    render(<ExamRunner view={view()} onFinished={() => {}} />);
    expect(screen.getByText(/còn 3 câu chưa làm/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Câu 3" }));
    for (const l of ["a", "b", "c", "d"]) fireEvent.click(screen.getByRole("button", { name: `${l} Đúng` }));
    fireEvent.click(screen.getByRole("button", { name: "Câu 4" }));
    fireEvent.change(screen.getByLabelText("Đáp án"), { target: { value: "2,5" } });
    expect(screen.getByText(/còn 1 câu chưa làm/)).toBeInTheDocument();
  });

  it("auto-submits when time runs out", async () => {
    const f = mockFetch((url) => (url.endsWith("/submit") ? { body: { status: "submitted" } } : undefined));
    const onFinished = vi.fn();
    render(<ExamRunner view={view(1500)} onFinished={onFinished} />);
    await act(async () => void vi.advanceTimersByTime(2500));
    await waitFor(() => expect(onFinished).toHaveBeenCalled());
    expect(f.mock.calls.some((c) => c[0] === "/api/attempts/att/submit")).toBe(true);
  });

  it("an answer after the deadline closes the exam", async () => {
    mockFetch((url, init) => (init?.method === "PUT" ? { status: 409, body: { error: { code: "attempt_closed", message: "Bài làm đã kết thúc" } } } : undefined));
    const onFinished = vi.fn();
    render(<ExamRunner view={view()} onFinished={onFinished} />);
    fireEvent.click(screen.getByTestId("option-A"));
    await act(async () => void vi.advanceTimersByTime(600));
    await waitFor(() => expect(onFinished).toHaveBeenCalled());
  });

  it("counts tab switches", async () => {
    const f = mockFetch(() => ({ body: {} }));
    render(<ExamRunner view={view()} onFinished={() => {}} />);
    Object.defineProperty(document, "visibilityState", { value: "hidden", configurable: true });
    document.dispatchEvent(new Event("visibilitychange"));
    await waitFor(() => expect(f.mock.calls.some((c) => c[0] === "/api/attempts/att/tab-switch")).toBe(true));
    Object.defineProperty(document, "visibilityState", { value: "visible", configurable: true });
  });
});
