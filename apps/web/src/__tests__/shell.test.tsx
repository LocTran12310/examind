import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "@/components/layout/AppShell/AppShell";
import { OrgSwitcher } from "@/components/layout/OrgSwitcher/OrgSwitcher";
import { mockFetch, renderWithQuery, route } from "./helpers";
import { ThemeProvider } from "@/components/layout/ThemeProvider/ThemeProvider";
import { activeItem, groupsFor, homeFor } from "@/lib/common/nav";
import type { Me } from "@/interfaces/auth.interface";

const router = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }));
vi.mock("next/navigation", () => ({ usePathname: () => "/org/exams/123", useRouter: () => router }));

const me = (role: Me["role"]): Me => ({ id: "u", username: "lan", full_name: "Cô Lan Anh", role, must_change_password: false, org: { id: "o", code: "trungtama", name: "Trung tâm A" } });
const shell = (role: Me["role"]) =>
  renderWithQuery(
    <ThemeProvider>
      <AppShell me={me(role)}>
        <p>nội dung</p>
      </AppShell>
    </ThemeProvider>,
  );

describe("navigation", () => {
  it("groups items by role", () => {
    // "Học tập" comes with the nesting HS ⊂ GV ⊂ Admin (ADR-02); nav.test.ts covers the containment itself
    expect(groupsFor("teacher").map((g) => g.label)).toEqual(["Đề & câu hỏi", "Lớp & học sinh", "Báo cáo", "Cài đặt", "Học tập"]);
    expect(groupsFor("teacher").flatMap((g) => g.items.map((i) => i.href))).not.toContain("/org/settings/ingestion");
    expect(groupsFor("super_admin").map((g) => g.label)).toEqual(["Cài đặt", "Hệ thống"]);
    expect(groupsFor("student").flatMap((g) => g.items.map((i) => i.href))).toEqual(["/home", "/me/stats"]);
    expect(homeFor("teacher")).toBe("/org/review");
    expect(activeItem("teacher", "/org/exams/123")?.label).toBe("Đề thi & giao bài");
  });
});

describe("AppShell", () => {
  it("shows the role's menu with the current page marked, and a breadcrumb", () => {
    shell("org_admin");
    const nav = screen.getByLabelText("Điều hướng chính");
    expect(within(nav).getByRole("link", { name: "Đề thi & giao bài" })).toHaveAttribute("aria-current", "page");
    expect(within(nav).getByRole("link", { name: "Cấu hình tách đề" })).toBeInTheDocument();
    expect(within(nav).queryByRole("link", { name: "Tổ chức" })).not.toBeInTheDocument();
    expect(screen.getByRole("banner")).toHaveTextContent("Đề & câu hỏi / Đề thi & giao bài");
  });

  it("uses the same shell for students", () => {
    shell("student");
    const nav = screen.getByLabelText("Điều hướng chính");
    expect(within(nav).getByRole("link", { name: "Bài được giao" })).toBeInTheDocument();
    expect(within(nav).queryByRole("link", { name: "Ngân hàng câu hỏi" })).not.toBeInTheDocument();
  });

  it("has the org selector, theme and user menu at the top right", async () => {
    shell("teacher");
    const header = screen.getByRole("banner");
    expect(within(header).getByRole("combobox", { name: "Chọn tổ chức" })).toHaveTextContent("Trung tâm A");
    expect(within(header).getByRole("button", { name: "Giao diện" })).toBeInTheDocument();
    await userEvent.click(within(header).getByRole("button", { name: "Tài khoản" }));
    const menu = await screen.findByRole("menu");
    expect(menu).toHaveTextContent("Cô Lan Anh");
    expect(menu).toHaveTextContent("Giáo viên");
    expect(within(menu).getByRole("menuitem", { name: "Đổi mật khẩu" })).toBeInTheDocument();
    expect(within(menu).getByRole("menuitem", { name: "Đăng xuất" })).toBeInTheDocument();
  });

  it("the org selector lists my orgs; switching calls the API, clears the query cache and navigates with the router", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign });
    const fetch = mockFetch(
      route("GET", "/api/me/orgs", [
        { id: "o", code: "trungtama", name: "Trung tâm A", role: "teacher", is_home: true },
        { id: "b", code: "ttb", name: "Trung tâm B", role: "org_admin", is_home: false },
      ]),
      route("POST", "/api/auth/switch-org", { ...me("org_admin"), org: { id: "b", code: "ttb", name: "Trung tâm B" } }),
    );
    const u = userEvent.setup();
    const { client } = renderWithQuery(<OrgSwitcher me={me("teacher")} />);
    client.setQueryData(["classes", "search", {}], { data: [], total: 0, page: 1, limit: 20 }); // a list of the old org
    const clear = vi.spyOn(client, "clear");
    await u.click(screen.getByRole("combobox", { name: "Chọn tổ chức" }));
    const b = await screen.findByRole("option", { name: /Trung tâm B/ });
    expect(b).toHaveTextContent("ttb · Quản trị trung tâm");
    await u.click(b);
    await waitFor(() => expect(router.push).toHaveBeenCalledWith("/org/review"));
    expect(router.refresh).toHaveBeenCalled();
    expect(clear).toHaveBeenCalled();
    expect(client.getQueryData(["classes", "search", {}])).toBeUndefined();
    expect(assign).not.toHaveBeenCalled();
    const call = fetch.mock.calls.find(([url]) => url === "/api/auth/switch-org");
    expect(JSON.parse(String((call?.[1] as RequestInit).body))).toEqual({ org_id: "b" });
    vi.unstubAllGlobals();
  });

  it("'Đăng xuất' ends the session, clears the query cache and opens the login page", async () => {
    const fetch = mockFetch(route("GET", "/api/me/orgs", []), route("POST", "/api/auth/logout", undefined, 204));
    const u = userEvent.setup();
    const { client } = shell("teacher");
    const clear = vi.spyOn(client, "clear");
    await u.click(within(screen.getByRole("banner")).getByRole("button", { name: "Tài khoản" }));
    await u.click(await screen.findByRole("menuitem", { name: "Đăng xuất" }));
    await waitFor(() => expect(router.push).toHaveBeenCalledWith("/login"));
    expect(fetch.mock.calls.some(([url, init]) => url === "/api/auth/logout" && (init as RequestInit)?.method === "POST")).toBe(true);
    expect(clear).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("a super admin inside an org keeps the Hệ thống menu", () => {
    expect(groupsFor("org_admin", true).map((g) => g.label)).toContain("Hệ thống");
    expect(groupsFor("org_admin", false).map((g) => g.label)).not.toContain("Hệ thống");
  });

  it("collapses the sidebar with the trigger", async () => {
    const { container } = shell("teacher");
    const wrapper = container.querySelector("[data-slot=sidebar]")!;
    expect(wrapper).toHaveAttribute("data-state", "expanded");
    await userEvent.click(screen.getByRole("button", { name: "Mở menu" }));
    expect(wrapper).toHaveAttribute("data-state", "collapsed");
  });
});
