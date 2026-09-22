import { render, screen, waitFor, within } from "@testing-library/react";
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

const qs = [
  { id: "q1", type: "mcq", stem: "Tọa độ đỉnh của parabol $y=x^2$ là **đúng**", options: [{ label: "A", content: "$(0;0)$" }], answer: { key: "A" }, solution: "", position: 1, points: 5, section: "I", topics: [], tags: [] },
  { id: "q2", type: "essay", stem: "Giải phương trình", options: [], answer: null, solution: "", position: 2, points: 5, section: "IV", topics: [], tags: [] },
] as unknown as Exam["questions"];

describe("exams list", () => {
  it("the list only fetches exams; a row shows its questions in the shared table, rendered", async () => {
    const fetch = mockFetch(
      route("GET", /^\/api\/exams\?/, page([exam(), exam({ id: "e2", title: "Đề thi thử THPT" })])),
      route("GET", /^\/api\/exams\/e1\/questions\?/, page(qs)),
    );
    const u = userEvent.setup();
    render(<ExamsPage />);
    await u.type(await screen.findByRole("textbox", { name: "Lọc Đề" }), "15");
    await waitFor(() => expect(lastQuery(fetch, "/exams").get("title")).toBe("15"), { timeout: 1500 });
    expect(fetch.mock.calls.some(([url]) => String(url).startsWith("/api/exams/e1"))).toBe(false);
    const row = screen.getByRole("button", { name: "Kiểm tra 15 phút" }).closest("tr")!;
    await u.click(within(row).getAllByRole("cell")[2]); // the row, not its title (the title opens the dialog)
    const cell = await screen.findByText(/Tọa độ đỉnh của parabol/);
    expect(cell.closest("td")!.querySelector(".katex")).not.toBeNull(); // formula rendered, not raw
    expect(cell.closest("td")!.querySelector("strong")).toHaveTextContent("đúng");
    expect(screen.getByText("Chi tiết · Kiểm tra 15 phút")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Soạn đề & giao bài/ })).toHaveAttribute("href", "/org/exams/e1");
    expect(lastQuery(fetch, "/exams/e1/questions").get("page")).toBe("1");
  });

  it("clicking the exam title opens a dialog with the whole exam, fetched on open", async () => {
    const fetch = mockFetch(route("GET", /^\/api\/exams\?/, page([exam()])), route("GET", "/api/exams/e1", exam({ questions: qs })));
    const u = userEvent.setup();
    render(<ExamsPage />);
    await u.click(await screen.findByRole("button", { name: "Kiểm tra 15 phút" }));
    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByTestId("preview-q-1")).toHaveTextContent("Câu 1 · Trắc nghiệm · 5 điểm");
    expect(within(dialog).getByText("Phần I")).toBeInTheDocument();
    expect(dialog.querySelector(".katex")).not.toBeNull();
    expect(fetch.mock.calls.filter(([url]) => url === "/api/exams/e1")).toHaveLength(1);
  });
});
