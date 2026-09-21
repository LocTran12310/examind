import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AssignDialog } from "@/components/exams/AssignDialog";
import { StudentHome } from "@/components/exams/StudentHome";
import type { MyAssignment, SchoolClass } from "@/lib/types";
import { mockFetch, route } from "./helpers";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

const klass: SchoolClass = { id: "c1", name: "10A1", grade: 10, school_year: "2026-2027", member_count: 30, created_at: "" };
const assignment = (title: string, o: Partial<MyAssignment> = {}): MyAssignment => ({
  assignment: { id: title, exam_id: "e", title, open_at: "2026-09-22T00:00:00Z", close_at: "2026-09-29T00:00:00Z", duration_minutes: 45,
    max_attempts: 1, shuffle_questions: true, shuffle_options: true, results_policy: "after_submit", students: 30, submitted: 0, classes: [] },
  state: "open", attempts: [], attempts_left: 1, ...o,
});

afterEach(() => vi.unstubAllGlobals());

describe("assign and student home", () => {
  it("assigns to a class with the window and policies", async () => {
    const f = mockFetch(route("POST", "/api/assignments", { id: "a1" }, 201));
    const onDone = vi.fn();
    render(<AssignDialog examId="e1" title="Kiểm tra" classes={[klass]} onDone={onDone} />);
    expect(screen.getByRole("button", { name: "Giao bài" })).toBeDisabled();
    await userEvent.click(screen.getByLabelText(/10A1/));
    await userEvent.selectOptions(screen.getByLabelText("Xem kết quả"), "after_close");
    await userEvent.click(screen.getByRole("button", { name: "Giao bài" }));
    await waitFor(() => expect(onDone).toHaveBeenCalled());
    const body = JSON.parse(String(f.mock.calls[0][1]?.body));
    expect(body).toMatchObject({ exam_id: "e1", class_ids: ["c1"], duration_minutes: 45, results_policy: "after_close", shuffle_options: true });
    expect(new Date(body.close_at).getTime()).toBeGreaterThan(new Date(body.open_at).getTime());
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
    render(<StudentHome />);
    expect(await screen.findByTestId("open-Đang mở")).toBeInTheDocument();
    expect(screen.getByTestId("upcoming-Sắp tới")).toBeInTheDocument();
    expect(screen.getByTestId("done-Đã làm")).toHaveTextContent("8 điểm");
    await userEvent.click(screen.getByRole("button", { name: "Bắt đầu" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/exam/att1"));
  });
});
