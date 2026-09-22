import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import TagsPage from "@/app/(app)/org/tags/page";
import { TagForm } from "@/components/page-components/Tags/TagForm/TagForm";
import { lastBody, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

beforeEach(() => setUrl("/org/tags"));
afterEach(() => vi.unstubAllGlobals());

describe("tags", () => {
  it("creates a tag in a group", async () => {
    const f = mockFetch(route("POST", "/api/tags", { id: "t" }, 201));
    const onDone = vi.fn();
    const u = userEvent.setup();
    render(<TagForm onDone={onDone} />);
    await u.click(screen.getByLabelText("Nhóm"));
    await u.click(await screen.findByRole("option", { name: "Kỹ năng" }));
    await u.type(screen.getByLabelText("Tên tag"), "đọc đồ thị");
    await u.click(screen.getByRole("button", { name: "Thêm tag" }));
    await waitFor(() => expect(onDone).toHaveBeenCalled());
    expect(JSON.parse(String(f.mock.calls.find(([u]) => u === "/api/tags")?.[1]?.body))).toEqual({ group: "skill", name: "đọc đồ thị", subject_id: null });
  });

  it("a tag belongs to the chosen subject; nguồn đề is always shared", async () => {
    const f = mockFetch(route("POST", "/api/tags", { id: "t" }, 201), route("GET", "/api/taxonomy", { subjects: [{ id: "s-toan", code: "toan", name: "Toán" }], grades: [], semesters: [] }));
    const onDone = vi.fn();
    const u = userEvent.setup();
    render(<TagForm onDone={onDone} subjectId="s-toan" />);
    await waitFor(() => expect(screen.getByLabelText("Môn")).toHaveTextContent("Toán"));
    await u.type(screen.getByLabelText("Tên tag"), "Đổi biến");
    await u.click(screen.getByRole("button", { name: "Thêm tag" }));
    await waitFor(() => expect(onDone).toHaveBeenCalled());
    const body = () => JSON.parse(String([...f.mock.calls].reverse().find(([url]) => url === "/api/tags")?.[1]?.body));
    expect(body()).toEqual({ group: "method", name: "Đổi biến", subject_id: "s-toan" });
    await u.click(screen.getByLabelText("Nhóm"));
    await u.click(await screen.findByRole("option", { name: "Nguồn đề" }));
    expect(screen.getByLabelText("Môn")).toHaveTextContent("Dùng chung mọi môn");
    await u.click(screen.getByRole("button", { name: "Thêm tag" }));
    await waitFor(() => expect(body()).toEqual({ group: "source", name: "Đổi biến", subject_id: null }));
  });

  it("shows the duplicate error", async () => {
    mockFetch(route("POST", "/api/tags", { code: "conflict", message: "Tag đã tồn tại trong nhóm này" }, 409));
    render(<TagForm onDone={() => {}} />);
    await userEvent.type(screen.getByLabelText("Tên tag"), "Đổi biến");
    await userEvent.click(screen.getByRole("button", { name: "Thêm tag" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Tag đã tồn tại trong nhóm này");
  });

  it("lists, filters by group on the server, renames and deletes; the list refetches by itself", async () => {
    const f = mockFetch(
      route("POST", "/api/tags/search", searchPage([{ id: "1", group: "method", name: "đổi biến" }])),
      route("PATCH", "/api/tags/1", { id: "1", group: "method", name: "Đổi biến số" }),
      route("DELETE", "/api/tags/1", undefined, 204),
    );
    const u = userEvent.setup();
    render(<TagsPage />);
    await screen.findByText("đổi biến");
    await u.click(screen.getByRole("combobox", { name: "Lọc Nhóm" }));
    await u.click(await screen.findByRole("option", { name: "Phương pháp" }));
    await waitFor(() => expect(lastBody(f, "/tags/search").filters).toEqual({ group: { value: "method" } }));
    expect(lastBody(f, "/tags/search").include_shared).toBe(false);
    const searches = () => f.mock.calls.filter(([url]) => url === "/api/tags/search").length;
    await u.click(screen.getByRole("checkbox", { name: "Chọn dòng" }));
    await u.click(screen.getByRole("button", { name: "Sửa" }));
    const input = await screen.findByLabelText("Tên tag");
    await u.clear(input);
    await u.type(input, "Đổi biến số");
    const beforeSave = searches();
    await u.click(screen.getByRole("button", { name: "Lưu" }));
    await waitFor(() => expect(f.mock.calls.some(([url]) => url === "/api/tags/1")).toBe(true));
    await waitFor(() => expect(searches()).toBeGreaterThan(beforeSave)); // TAG_KEYS.ALL invalidated, no reloadKey
    // the row stays selected across the refetch
    await u.click(screen.getByRole("button", { name: "Xóa" }));
    const beforeDelete = searches();
    await u.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xóa" }));
    await waitFor(() => expect(f.mock.calls.some(([url, init]) => url === "/api/tags/1" && (init as RequestInit)?.method === "DELETE")).toBe(true));
    await waitFor(() => expect(searches()).toBeGreaterThan(beforeDelete));
  });

  it("the subject column is a resource parameter", async () => {
    const f = mockFetch(route("POST", "/api/tags/search", searchPage([])), route("GET", "/api/taxonomy", { subjects: [{ id: "s-toan", code: "toan", name: "Toán" }], grades: [], semesters: [] }));
    const u = userEvent.setup();
    render(<TagsPage />);
    await u.click(await screen.findByRole("combobox", { name: "Lọc Môn" }));
    await u.click(await screen.findByRole("option", { name: "Dùng chung" }));
    await waitFor(() => expect(lastBody(f, "/tags/search").subject_id).toBe("shared"));
    expect(lastBody(f, "/tags/search").filters).toBeUndefined();
  });
});
