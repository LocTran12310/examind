import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ClassesPage from "@/app/(app)/org/classes/page";
import { ClassForm } from "@/components/page-components/Classes/ClassForm/ClassForm";
import { MemberManager } from "@/components/page-components/Classes/MemberManager/MemberManager";
import { currentSchoolYear } from "@/lib/page-libs/classes/school-year";
import type { SchoolClass, User } from "@/lib/types";
import { lastBody, lastQuery, mockFetch, page, renderWithQuery as render, route, searchPage } from "./helpers";
import { searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const student = (username: string, class_ids: string[] = []): User => ({
  id: username,
  username,
  full_name: username.toUpperCase(),
  email: null,
  role: "student",
  is_active: true,
  must_change_password: false,
  last_login_at: null,
  created_at: "",
  class_ids,
});
const klass = (o: Partial<SchoolClass> = {}): SchoolClass => ({ id: "c1", name: "10A1", grade: 10, school_year: "2026-2027", member_count: 1, created_at: "", ...o });

beforeEach(() => setUrl("/org/classes"));
afterEach(() => vi.unstubAllGlobals());

describe("classes", () => {
  it("school year rolls over in August", () => {
    expect(currentSchoolYear(new Date(2026, 8, 1))).toBe("2026-2027");
    expect(currentSchoolYear(new Date(2027, 2, 1))).toBe("2026-2027");
  });

  it("creates a class with a grade picked by level", async () => {
    const f = mockFetch(
      route("POST", "/api/classes", { id: "c" }, 201),
      route("POST", "/api/school-levels/search", searchPage([{ id: "thpt", code: "thpt", name: "Trung học phổ thông", grade_from: 10, grade_to: 12, sort: 1, grade_count: 1 }])),
      route("POST", "/api/grades/search", searchPage([{ id: "g10", level: 10, name: "Lớp 10", school_level_id: "thpt", class_count: 0 }])),
    );
    const onDone = vi.fn();
    const u = userEvent.setup();
    render(<ClassForm onDone={onDone} />);
    await u.type(screen.getByLabelText("Tên lớp"), "10A1");
    await u.click(screen.getByLabelText("Khối"));
    const listbox = await screen.findByRole("listbox");
    expect(within(listbox).getByText("Trung học phổ thông")).toBeInTheDocument();
    await u.click(within(listbox).getByRole("option", { name: "Lớp 10" }));
    await u.click(screen.getByRole("button", { name: "Tạo lớp" }));
    await waitFor(() => expect(onDone).toHaveBeenCalled());
    const post = f.mock.calls.find(([url, init]) => url === "/api/classes" && (init as RequestInit)?.method === "POST");
    expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({ name: "10A1", grade_id: "g10" });
  });

  it("selecting a class shows its students in a detail table with its own URL params", async () => {
    const fetch = mockFetch(
      route("POST", "/api/classes/search", searchPage([klass(), klass({ id: "c2", name: "11B", grade: 11 })])),
      route("GET", /^\/api\/users\?.*class_id=c1/, page([student("hs01", ["c1"])])),
    );
    const u = userEvent.setup();
    render(<ClassesPage />);
    await u.click(await screen.findByText("10A1"));
    expect(await screen.findByText("HS01")).toBeInTheDocument();
    expect(lastQuery(fetch, "/users").get("class_id")).toBe("c1");
    // jsdom has no layout, so the resize handle's hit-test claims every pointer down; set the value directly
    fireEvent.change(screen.getAllByRole("textbox", { name: "Lọc Họ tên" })[0], { target: { value: "an" } });
    await waitFor(() => expect(searchOf().get("m.full_name")).toBe("an"), { timeout: 1500 });
    await waitFor(() => expect(lastQuery(fetch, "/users").get("full_name")).toBe("an"));
    expect(lastBody(fetch, "/classes/search").filters).toBeUndefined(); // the member filter stays on the member table
  });

  it("adds a student and removes one after confirmation", async () => {
    const f = mockFetch(
      route("GET", /^\/api\/users\?.*class_id=c1/, page([student("hs01", ["c1"])])),
      route("GET", /^\/api\/users\?q=hs/, page([student("hs01", ["c1"]), student("hs02")])),
      route("POST", "/api/classes/c1/members", undefined, 204),
      route("DELETE", "/api/classes/c1/members/hs01", undefined, 204),
    );
    const u = userEvent.setup();
    render(<MemberManager classId="c1" />);
    await screen.findByText("HS01");
    await u.click(screen.getByRole("button", { name: "Thêm học sinh" }));
    await u.type(screen.getByRole("textbox", { name: "Tìm học sinh" }), "hs");
    const dialog = await screen.findByRole("dialog");
    await u.click(await within(dialog).findByRole("button", { name: "Thêm" }));
    await waitFor(() => expect(f.mock.calls.some((c) => c[0] === "/api/classes/c1/members")).toBe(true));
    await waitFor(() => expect(within(dialog).queryByRole("button", { name: "Thêm" })).toBeNull()); // hs02 leaves the list once added
    expect(JSON.parse(String(f.mock.calls.find((c) => c[0] === "/api/classes/c1/members")?.[1]?.body)).user_ids).toEqual(["hs02"]);
    await u.keyboard("{Escape}");
    await u.click(screen.getByRole("checkbox", { name: "Chọn dòng" }));
    await u.click(screen.getByRole("button", { name: "Xóa" }));
    await u.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xóa" }));
    await waitFor(() => expect(f.mock.calls.some(([url, init]) => url === "/api/classes/c1/members/hs01" && (init as RequestInit)?.method === "DELETE")).toBe(true));
  });
});
