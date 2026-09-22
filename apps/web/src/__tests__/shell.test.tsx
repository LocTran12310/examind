import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "@/app/(app)/AppShell";
import { ThemeProvider } from "@/components/app/ThemeProvider";
import { activeItem, groupsFor, homeFor } from "@/lib/nav";
import type { Me } from "@/lib/types";

vi.mock("next/navigation", () => ({ usePathname: () => "/org/exams/123", useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }) }));

const me = (role: Me["role"]): Me => ({ id: "u", username: "lan", full_name: "Cô Lan Anh", role, must_change_password: false, org: { id: "o", code: "trungtama", name: "Trung tâm A" } });
const shell = (role: Me["role"]) =>
  render(
    <ThemeProvider>
      <AppShell me={me(role)}>
        <p>nội dung</p>
      </AppShell>
    </ThemeProvider>,
  );

describe("navigation", () => {
  it("groups items by role", () => {
    expect(groupsFor("teacher").map((g) => g.label)).toEqual(["Đề & câu hỏi", "Lớp & học sinh", "Báo cáo", "Cài đặt"]);
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

  it("collapses the sidebar with the trigger", async () => {
    const { container } = shell("teacher");
    const wrapper = container.querySelector("[data-slot=sidebar]")!;
    expect(wrapper).toHaveAttribute("data-state", "expanded");
    await userEvent.click(screen.getByRole("button", { name: "Mở menu" }));
    expect(wrapper).toHaveAttribute("data-state", "collapsed");
  });
});
