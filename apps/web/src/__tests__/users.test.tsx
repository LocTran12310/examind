import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MeProvider } from "@/app/(app)/AppShell";
import UsersPage from "@/app/(app)/org/users/page";
import { rolesManagedBy, UserCreateForm } from "@/components/org/UserForm";
import type { User } from "@/lib/types";
import { lastQuery, me, mockFetch, page, route } from "./helpers";
import { searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const user = (o: Partial<User>): User => ({
  id: "u1",
  username: "hs01",
  full_name: "Học Sinh",
  email: null,
  role: "student",
  is_active: true,
  must_change_password: false,
  last_login_at: null,
  created_at: "2026-09-21T00:00:00Z",
  class_ids: [],
  ...o,
});
const classes = page([{ id: "c1", name: "10A1", school_year: "2026-2027", grade: 10, member_count: 2 }]);
const users = [user({ id: "me", username: "admin", full_name: "Quản Trị", role: "org_admin" }), user({ id: "s", username: "hs01", full_name: "Bùi Văn Châu", is_active: false, class_ids: ["c1"] })];

function renderPage(role: "org_admin" | "teacher" = "org_admin") {
  return render(
    <MeProvider value={me(role)}>
      <UsersPage />
    </MeProvider>,
  );
}

beforeEach(() => setUrl("/org/users"));
afterEach(() => vi.unstubAllGlobals());

describe("users", () => {
  it("teachers can only create students", () => {
    expect(rolesManagedBy("teacher")).toEqual(["student"]);
    expect(rolesManagedBy("org_admin")).toContain("teacher");
  });

  it("creates a user and shows the temp password once", async () => {
    mockFetch(route("POST", "/api/users", { user: user({ username: "nguyenvanan" }), temp_password: "Pw23456789" }, 201));
    render(<UserCreateForm myRole="org_admin" orgCode="trungtama" onDone={() => {}} />);
    await userEvent.type(screen.getByLabelText("Họ tên"), "Nguyễn Văn An");
    await userEvent.click(screen.getByRole("button", { name: "Tạo tài khoản" }));
    expect(await screen.findByTestId("temp-cred")).toHaveTextContent("trungtama / nguyenvanan / Pw23456789");
  });

  it("lists users from the server with class names and status", async () => {
    mockFetch(route("GET", /^\/api\/users\?/, page(users)), route("GET", /^\/api\/classes\?/, classes));
    renderPage();
    const row = (await screen.findByText("Bùi Văn Châu")).closest("tr")!;
    expect(row).toHaveTextContent("10A1");
    expect(row).toHaveTextContent("Đã khóa");
    expect(screen.getByRole("columnheader", { name: /Vai trò/ })).toBeInTheDocument();
  });

  it("filters by class on the server and keeps it in the URL", async () => {
    const fetch = mockFetch(route("GET", /^\/api\/users\?/, page(users)), route("GET", /^\/api\/classes\?/, classes));
    const u = userEvent.setup();
    renderPage();
    await screen.findByText("Bùi Văn Châu");
    await u.click(screen.getByRole("combobox", { name: "Lọc Lớp" }));
    await u.click(await screen.findByRole("option", { name: "10A1 (2026-2027)" }));
    await waitFor(() => expect(lastQuery(fetch, "/users").get("class_id")).toBe("c1"));
    expect(searchOf().get("class_id")).toBe("c1");
  });

  it("teachers do not see the role column", async () => {
    mockFetch(route("GET", /^\/api\/users\?/, page(users)), route("GET", /^\/api\/classes\?/, classes));
    renderPage("teacher");
    await screen.findByText("Bùi Văn Châu");
    expect(screen.queryByRole("columnheader", { name: /Vai trò/ })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Học sinh" })).toBeInTheDocument();
  });

  it("toolbar: unlock the selected user; reset password asks first; never lock myself", async () => {
    const fetch = mockFetch(
      route("GET", /^\/api\/users\?/, page(users)),
      route("GET", /^\/api\/classes\?/, classes),
      route("PATCH", "/api/users/s", user({ id: "s", is_active: true })),
      route("POST", "/api/users/s/reset-password", { user_id: "s", username: "hs01", full_name: "Bùi Văn Châu", temp_password: "Tmp1234567" }),
    );
    const u = userEvent.setup();
    renderPage();
    await screen.findByText("Bùi Văn Châu");
    const [mine, student] = screen.getAllByRole("checkbox", { name: "Chọn dòng" });
    await u.click(mine);
    expect(screen.getByRole("button", { name: "Khóa" })).toBeDisabled();
    await u.click(mine);
    await u.click(student);
    await u.click(screen.getByRole("button", { name: "Mở khóa" }));
    await waitFor(() => expect(fetch.mock.calls.some(([url, init]) => url === "/api/users/s" && (init as RequestInit)?.method === "PATCH")).toBe(true));
    // the table reloads after a change and clears the selection
    await waitFor(() => expect(screen.getByRole("button", { name: "Đặt lại mật khẩu" })).toBeDisabled());
    await u.click(screen.getAllByRole("checkbox", { name: "Chọn dòng" })[1]);
    await u.click(screen.getByRole("button", { name: "Đặt lại mật khẩu" }));
    const confirm = await screen.findByRole("alertdialog");
    await u.click(within(confirm).getByRole("button", { name: "Đặt lại" }));
    expect(await screen.findByTestId("temp-cred")).toHaveTextContent("trungtama / hs01 / Tmp1234567");
  });
});
