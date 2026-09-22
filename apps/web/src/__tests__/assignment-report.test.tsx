import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AssignmentReportPage } from "@/components/page-components/AssignmentReport/AssignmentReportPage";
import type { AssignmentReport } from "@/interfaces/assignment.interface";
import { pct } from "@/lib/page-libs/assignment-report/pct";
import { mockFetch, renderWithQuery, route } from "./helpers";

const report: AssignmentReport = {
  assignment_id: "a", title: "Kiểm tra", submitted: 1, total_students: 2, average: 7.5,
  distribution: Array.from({ length: 10 }, (_, i) => ({ from: i, to: i + 1, count: i === 7 ? 1 : 0 })),
  students: [
    { student_id: "1", full_name: "An", username: "an", status: "submitted", attempt_id: "t1", score10: 7.5, needs_grading: true, tab_switches: 3 },
    { student_id: "2", full_name: "Bình", username: "binh", status: "not_started", attempt_id: null, score10: null, needs_grading: false, tab_switches: 0 },
  ],
  questions: [{ question_id: "q", position: 1, type: "mcq", stem: "Đề 1", answered: 1, ratio: 0.5, top_wrong: { label: "C", count: 1 } }],
};

afterEach(() => vi.unstubAllGlobals());

describe("assignment report", () => {
  it("loads the report and renders totals, students and per-question stats", async () => {
    mockFetch(route("GET", "/api/assignments/a/report", report));
    renderWithQuery(<AssignmentReportPage id="a" />);
    expect(await screen.findByTestId("submitted")).toHaveTextContent("1/2");
    expect(screen.getByRole("heading", { name: "Kiểm tra" })).toBeInTheDocument();
    expect(screen.getByTestId("average")).toHaveTextContent("7.5");
    expect(screen.getByTestId("st-an")).toHaveTextContent("Cần chấm tự luận");
    expect(screen.getByRole("link", { name: "Xem bài" })).toHaveAttribute("href", "/results/t1");
    expect(screen.getByTestId("st-binh")).toHaveTextContent("Chưa làm");
    expect(screen.getByTestId("qs-1")).toHaveTextContent("50%");
    expect(screen.getByTestId("qs-1")).toHaveTextContent("Hay chọn sai: C (1)");
    expect(pct(null)).toBe("—");
  });
});
