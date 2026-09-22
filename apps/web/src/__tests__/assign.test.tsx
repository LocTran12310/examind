import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AssignDialog } from "@/components/page-components/ExamDetail/AssignDialog/AssignDialog";
import { ExamDetailPage } from "@/components/page-components/ExamDetail/ExamDetailPage";
import { StudentAssignments } from "@/components/page-components/StudentHome/StudentAssignments/StudentAssignments";
import type { Assignment, MyAssignment } from "@/interfaces/assignment.interface";
import type { SchoolClass } from "@/interfaces/class.interface";
import type { Exam } from "@/interfaces/exam.interface";
import { toBusinessInput } from "@/lib/datetime";
import { lastBody, mockFetch, renderWithQuery, route, searchPage } from "./helpers";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, replace: vi.fn() }) }));

const klass: SchoolClass = { id: "c1", name: "10A1", grade: 10, school_year: "2026-2027", member_count: 30, created_at: "" };
const base: Assignment = { id: "a1", exam_id: "e1", title: "Kiểm tra", open_at: "2026-09-22T00:00:00Z", close_at: "2026-09-29T00:00:00Z", duration_minutes: 45,
  max_attempts: 1, shuffle_questions: true, shuffle_options: true, results_policy: "after_submit", students: 30, submitted: 12, classes: ["10A1", "10A2"] };
const assignment = (title: string, o: Partial<MyAssignment> = {}): MyAssignment => ({
  assignment: { ...base, id: title, exam_id: "e", title, submitted: 0, classes: [] }, state: "open", attempts: [], attempts_left: 1, ...o,
});
const exam: Exam = { id: "e1", title: "Kiểm tra 15 phút", subject_id: null, grade: 10, description: "",
  settings: { points_by_type: { mcq: 0.25, true_false: 1, short_answer: 0.5, essay: 1 }, scale_to: 10 },
  blueprint: [], source: "manual", question_count: 0, total_points: 0, created_at: "", questions: [] };

afterEach(() => vi.unstubAllGlobals());

describe("assign and student home", () => {
  it("assigns to a class with the window (UTC on the wire) and policies", async () => {
    const f = mockFetch(route("POST", "/api/assignments", base, 201));
    const onDone = vi.fn();
    renderWithQuery(<AssignDialog examId="e1" title="Kiểm tra" classes={[klass]} onDone={onDone} />);
    expect(screen.getByRole("button", { name: "Giao bài" })).toBeDisabled();
    await userEvent.click(screen.getByLabelText(/10A1/));
    await userEvent.click(screen.getByRole("combobox", { name: "Xem kết quả" }));
    await userEvent.click(await screen.findByRole("option", { name: "Sau khi đóng bài" }));
    expect(screen.getByRole("combobox", { name: "Xem kết quả" })).toHaveTextContent("Sau khi đóng bài");
    await userEvent.click(screen.getByRole("button", { name: "Giao bài" }));
    await waitFor(() => expect(onDone).toHaveBeenCalledWith(base));
    const body = lastBody(f, "/assignments");
    expect(body).toMatchObject({ exam_id: "e1", title: "Kiểm tra", class_ids: ["c1"], duration_minutes: 45, max_attempts: 1, results_policy: "after_close", shuffle_options: true, shuffle_questions: true });
    for (const k of ["open_at", "close_at"]) expect(String(body[k])).toMatch(/^\d{4}-\d\d-\d\dT\d\d:\d\d:00\.000Z$/);
    // the picker shows business time; the instant sent is the same minute
    expect(toBusinessInput(String(body.open_at))).toBe(toBusinessInput(new Date()));
    expect(new Date(String(body.close_at)).getTime() - new Date(String(body.open_at)).getTime()).toBe(7 * 86400_000);
  });

  it("a server refusal shows its message and field errors", async () => {
    mockFetch(route("POST", "/api/assignments", { code: "validation_error", message: "Dữ liệu không hợp lệ", details: { fields: { close_at: "Phải sau giờ mở" } } }, 422));
    renderWithQuery(<AssignDialog examId="e1" title="Kiểm tra" classes={[klass]} onDone={vi.fn()} />);
    await userEvent.click(screen.getByLabelText(/10A1/));
    await userEvent.click(screen.getByRole("button", { name: "Giao bài" }));
    expect(await screen.findByText("Dữ liệu không hợp lệ")).toBeInTheDocument();
    expect(screen.getByText("Phải sau giờ mở")).toBeInTheDocument();
  });

  it("the exam page lists its assignments from /assignments/search filtered by exam", async () => {
    const f = mockFetch(
      route("GET", "/api/exams/e1", exam),
      route("GET", "/api/topics", []),
      route("POST", "/api/tags/search", searchPage([])),
      route("POST", "/api/classes/search", searchPage([klass])),
      route("POST", "/api/assignments/search", searchPage([base])),
    );
    renderWithQuery(<ExamDetailPage id="e1" />);
    const list = await screen.findByTestId("assigned");
    expect(within(list).getByRole("link", { name: "Kiểm tra" })).toHaveAttribute("href", "/org/assignments/a1");
    expect(list).toHaveTextContent("10A1, 10A2");
    expect(list).toHaveTextContent("12/30 đã nộp");
    expect(lastBody(f, "/assignments/search")).toEqual({ page: 1, limit: 1000, filters: { exam_id: { value: "e1" } } });
  });

  it("home shows open/upcoming/done and starts an attempt", async () => {
    mockFetch(
      route("GET", "/api/me/assignments", [
        assignment("Đang mở"),
        assignment("Sắp tới", { state: "upcoming" }),
        assignment("Đã làm", { attempts_left: 0, attempts: [{ id: "t1", status: "submitted", started_at: "", deadline_at: "", submitted_at: "2026-09-22T01:00:00Z", score: 2, max_score: 2.5, score10: 8, needs_grading: false }] }),
      ]),
      route("POST", "/api/assignments/Đang mở/start", { attempt_id: "att1" }),
    );
    renderWithQuery(<StudentAssignments />);
    expect(await screen.findByTestId("open-Đang mở")).toBeInTheDocument();
    expect(screen.getByTestId("upcoming-Sắp tới")).toBeInTheDocument();
    expect(screen.getByTestId("done-Đã làm")).toHaveTextContent("8 điểm");
    expect(screen.getByRole("link", { name: "Xem kết quả" })).toHaveAttribute("href", "/results/t1");
    await userEvent.click(screen.getByRole("button", { name: "Bắt đầu" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/exam/att1"));
  });
});
