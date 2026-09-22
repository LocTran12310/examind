import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ExamsPage from "@/app/(app)/org/exams/page";
import type { Exam } from "@/lib/types";
import { lastQuery, mockFetch, page, route } from "./helpers";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const exam = (o: Partial<Exam> = {}): Exam => ({
  id: "e1", title: "Kiểm tra 15 phút", subject_id: null, grade: 10, description: "", settings: { points_by_type: {} as Exam["settings"]["points_by_type"], scale_to: 10 },
  blueprint: [], source: "manual", question_count: 2, total_points: 10, created_at: "2026-09-22T00:00:00Z", questions: [], ...o,
});

beforeEach(() => setUrl("/org/exams"));

describe("exams list", () => {
  it("filters on the server and shows the selected exam's questions in the detail panel", async () => {
    const fetch = mockFetch(
      route("GET", /^\/api\/exams\?/, page([exam(), exam({ id: "e2", title: "Đề thi thử THPT" })])),
      route("GET", "/api/exams/e1", exam({
        questions: [
          { id: "q1", type: "mcq", stem: "Tọa độ đỉnh của parabol $y=x^2$ là", position: 1, points: 5 },
          { id: "q2", type: "essay", stem: "Giải phương trình", position: 2, points: 5 },
        ] as unknown as Exam["questions"],
      })),
    );
    const u = userEvent.setup();
    render(<ExamsPage />);
    await u.type(await screen.findByRole("textbox", { name: "Lọc Đề" }), "15");
    await waitFor(() => expect(lastQuery(fetch, "/exams").get("title")).toBe("15"), { timeout: 1500 });
    await u.click(screen.getByText("Kiểm tra 15 phút"));
    expect(await screen.findByText("Tọa độ đỉnh của parabol y=x^2 là")).toBeInTheDocument();
    expect(screen.getByText("Chi tiết · Kiểm tra 15 phút")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Soạn đề & giao bài/ })).toHaveAttribute("href", "/org/exams/e1");
  });
});
