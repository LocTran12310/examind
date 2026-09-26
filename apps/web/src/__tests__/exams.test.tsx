import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ExamsRoute from "@/app/(app)/org/exams/page";
import type { Exam } from "@/interfaces/exam.interface";
import { lastBody, mockFetch, renderWithQuery, route, searchPage } from "./helpers";
import { currentUrl, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const exam = (o: Partial<Exam> = {}): Exam => ({
  id: "e1", title: "Kiểm tra 15 phút", subject_id: null, grade: 10, description: "", settings: { points_by_type: {} as Exam["settings"]["points_by_type"], scale_to: 10 },
  blueprint: [], source: "manual", question_count: 2, total_points: 10, created_at: "2026-09-22T00:00:00Z", questions: [], ...o,
});

beforeEach(() => setUrl("/org/exams"));
afterEach(() => vi.unstubAllGlobals());

const qs = [
  { id: "q1", type: "mcq", stem: "Tọa độ đỉnh của parabol $y=x^2$ là **đúng**", options: [{ label: "A", content: "$(0;0)$" }], answer: { key: "A" }, solution: "", position: 1, points: 5, section: "I", topics: [], tags: [] },
  { id: "q2", type: "essay", stem: "Giải phương trình", options: [], answer: null, solution: "", position: 2, points: 5, section: "IV", topics: [], tags: [] },
] as unknown as Exam["questions"];

const calls = (fetch: { mock: { calls: unknown[][] } }, url: string) => fetch.mock.calls.filter(([u]) => u === url);

describe("exams list", () => {
  it("posts /exams/search with the URL filters; a row shows its questions in the shared table, rendered", async () => {
    const fetch = mockFetch(
      route("POST", "/api/exams/search", searchPage([exam(), exam({ id: "e2", title: "Đề thi thử THPT" })])),
      route("POST", "/api/exams/e1/questions/search", searchPage(qs)),
    );
    const u = userEvent.setup();
    renderWithQuery(<ExamsRoute />);
    await u.type(await screen.findByRole("textbox", { name: "Lọc Đề" }), "15");
    await waitFor(() => expect(lastBody(fetch, "/exams/search").filters).toEqual({ title: { value: "15" } }), { timeout: 1500 });
    expect(currentUrl()).toContain("title=15");
    expect(fetch.mock.calls.some(([url]) => String(url).startsWith("/api/exams/e1"))).toBe(false);
    const row = screen.getByRole("button", { name: "Kiểm tra 15 phút" }).closest("tr")!;
    await u.click(within(row).getAllByRole("cell")[2]); // the row, not its title (the title opens the dialog)
    const cell = await screen.findByText(/Tọa độ đỉnh của parabol/);
    expect(cell.closest("td")!.querySelector(".katex")).not.toBeNull(); // formula rendered, not raw
    expect(cell.closest("td")!.querySelector("strong")).toHaveTextContent("đúng");
    expect(screen.getByText("Chi tiết · Kiểm tra 15 phút")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Soạn đề & giao bài/ })).toHaveAttribute("href", "/org/exams/e1");
    // the exam goes into the path, not into the body
    expect(lastBody(fetch, "/exams/e1/questions/search")).toEqual({ page: 1, limit: 20 });
    expect(calls(fetch, "/api/exams/e1")).toHaveLength(0);
  });

  it("clicking the exam title opens a dialog with the whole exam, fetched only then", async () => {
    const fetch = mockFetch(route("POST", "/api/exams/search", searchPage([exam()])), route("GET", "/api/exams/e1", exam({ questions: qs })));
    const u = userEvent.setup();
    renderWithQuery(<ExamsRoute />);
    const title = await screen.findByRole("button", { name: "Kiểm tra 15 phút" });
    expect(calls(fetch, "/api/exams/e1")).toHaveLength(0);
    await u.click(title);
    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByTestId("preview-q-1")).toHaveTextContent("Câu 1 · Trắc nghiệm · 5 điểm");
    expect(within(dialog).getByText("Phần I")).toBeInTheDocument();
    expect(dialog.querySelector(".katex")).not.toBeNull();
    expect(calls(fetch, "/api/exams/e1")).toHaveLength(1);
  });

  it("tab theo môn: mỗi tab mang số của nó, và chọn tab là đổi phạm vi chứ không phải thêm một bộ lọc", async () => {
    // hai cách nói cùng một điều là hai cách để chúng nói khác nhau: môn là phạm vi (tab), cột chỉ để đọc
    const fetch = mockFetch(
      route("GET", "/api/taxonomy", { subjects: [{ id: "s1", code: "toan", name: "Toán" }, { id: "s2", code: "ly", name: "Vật lý" }], grades: [], semesters: [] }),
      route("POST", "/api/exams/facets", { subjects: { s1: 30, none: 6 } }),
      route("POST", "/api/exams/search", searchPage([exam({ subject_id: "s1" })])),
    );
    const u = userEvent.setup();
    renderWithQuery(<ExamsRoute />);
    const tabs = await screen.findByRole("tablist", { name: "Môn học" });
    // Vật lý giữ 0 đề nên không chiếm chỗ; "Tất cả" mang tổng, "Chưa phân môn" chỉ hiện khi có đề như thế
    await waitFor(() => expect([...within(tabs).getAllByRole("tab")].map((t) => t.textContent)).toEqual(["Tất cả36", "Toán30", "Chưa phân môn 6"]));
    await u.click(within(tabs).getByRole("tab", { name: /Chưa phân môn/ }));
    // "none" đi ở đầu thân yêu cầu như một phạm vi, không nằm trong filters
    await waitFor(() => expect(lastBody(fetch, "/exams/search").subject_id).toBe("none"));
    expect((lastBody(fetch, "/exams/search").filters as Record<string, unknown> | undefined)?.subject_id).toBeUndefined();
    expect(currentUrl()).toContain("subject_id=none");
  });

  it("the list says which subject each paper is for (AC-01)", async () => {
    // the exam has carried a subject and the endpoint has filtered by it all along; the list never showed it,
    // so with two subjects in the bank this screen would be one undifferentiated pile
    mockFetch(
      route("GET", "/api/taxonomy", { subjects: [{ id: "s1", code: "toan", name: "Toán" }, { id: "s2", code: "ly", name: "Vật lý" }], grades: [], semesters: [] }),
      route("POST", "/api/exams/facets", { subjects: { s1: 1, none: 1 } }),
      route("POST", "/api/exams/search", searchPage([exam({ subject_id: "s1" }), exam({ id: "e2", title: "Đề Lý", subject_id: null })])),
    );
    renderWithQuery(<ExamsRoute />);
    await screen.findByRole("button", { name: "Kiểm tra 15 phút" });
    const subjectOf = (title: string) =>
      [...document.querySelectorAll("tbody tr")].find((r) => r.textContent?.includes(title))?.querySelectorAll("td")[2]?.textContent;
    expect(subjectOf("Kiểm tra 15 phút")).toBe("Toán");
    // an exam with no subject says so with a dash instead of an empty cell
    expect(subjectOf("Đề Lý")).toBe("—");
  });

  it("creates an exam and opens it", async () => {
    const fetch = mockFetch(
      route("POST", "/api/exams/search", searchPage([exam(), exam({ id: "e2", title: "Đề thi thử THPT" })])),
      route("POST", "/api/exams", exam({ id: "e9", title: "Đề mới" }), 201),
    );
    const u = userEvent.setup();
    renderWithQuery(<ExamsRoute />);
    await screen.findByRole("button", { name: "Kiểm tra 15 phút" });
    await u.click(screen.getByRole("button", { name: /Tạo đề/ }));
    await u.type(await screen.findByLabelText("Tên đề"), "Đề mới");
    await u.click(screen.getByRole("button", { name: "Tạo và soạn đề" }));
    await waitFor(() => expect(currentUrl()).toBe("/org/exams/e9"));
    // both labels are optional (A-02): left alone they go as null rather than being dropped, so the server is
    // told "no subject" instead of "unchanged"
    expect(lastBody(fetch, "/exams")).toEqual({ title: "Đề mới", subject_id: null, grade: null });
  });

  it("creates it with the subject and the grade, so the list can classify it at all (AC-01)", async () => {
    // the reported hole: 0 of 131 exams had a grade because this form only ever asked for a title, and the
    // "Lớp" column of the list was empty on every single row
    const fetch = mockFetch(
      route("POST", "/api/exams/search", searchPage([exam()])),
      route("GET", "/api/taxonomy", { subjects: [{ id: "s1", code: "toan", name: "Toán" }], grades: [{ id: "g11", level: 11, name: "Lớp 11" }], semesters: [] }),
      route("POST", "/api/exams", exam({ id: "e9", title: "Đề mới", subject_id: "s1", grade: 11 }), 201),
    );
    const u = userEvent.setup();
    renderWithQuery(<ExamsRoute />);
    await screen.findByRole("button", { name: "Kiểm tra 15 phút" });
    await u.click(screen.getByRole("button", { name: /Tạo đề/ }));
    await u.type(await screen.findByLabelText("Tên đề"), "Đề mới");
    await u.click(screen.getByRole("combobox", { name: "Môn" }));
    await u.click(await screen.findByRole("option", { name: "Toán" }));
    await u.click(screen.getByRole("combobox", { name: "Lớp" }));
    await u.click(await screen.findByRole("option", { name: "Lớp 11" }));
    await u.click(screen.getByRole("button", { name: "Tạo và soạn đề" }));
    // the grade goes as the number the organisation teaches, like every other grade field in the app
    await waitFor(() => expect(lastBody(fetch, "/exams")).toEqual({ title: "Đề mới", subject_id: "s1", grade: 11 }));
  });

  it("deletes the selected exams and refreshes the list", async () => {
    const fetch = mockFetch(
      route("POST", "/api/exams/search", searchPage([exam(), exam({ id: "e2", title: "Đề thi thử THPT" })])),
      route("DELETE", /^\/api\/exams\/e[12]$/, undefined, 204),
    );
    const u = userEvent.setup();
    renderWithQuery(<ExamsRoute />);
    await screen.findByRole("button", { name: "Kiểm tra 15 phút" });
    const before = calls(fetch, "/api/exams/search").length;
    for (const box of screen.getAllByRole("checkbox", { name: "Chọn dòng" })) await u.click(box);
    await u.click(screen.getByRole("button", { name: "Xóa" }));
    const confirm = await screen.findByRole("alertdialog");
    expect(confirm).toHaveTextContent("Xóa 2 đề thi?");
    await u.click(within(confirm).getByRole("button", { name: "Xóa" }));
    await waitFor(() => expect(fetch.mock.calls.filter(([, i]) => (i as RequestInit | undefined)?.method === "DELETE")).toHaveLength(2));
    await waitFor(() => expect(calls(fetch, "/api/exams/search").length).toBeGreaterThan(before)); // refreshed by the mutation
  });
});
