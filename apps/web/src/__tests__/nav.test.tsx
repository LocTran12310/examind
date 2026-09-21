import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AppShell, Sidebar } from "@/app/(app)/AppShell";
import { groupsFor, homeFor } from "@/lib/nav";
import type { Me } from "@/lib/types";

vi.mock("next/navigation", () => ({ usePathname: () => "/org/bank" }));

const me = (role: Me["role"]): Me => ({ id: "u", username: "u", full_name: "Cô Lan", role, must_change_password: false, org: { id: "o", code: "tt", name: "TT" } });

describe("navigation", () => {
  it("groups items by role", () => {
    expect(groupsFor("teacher").map((g) => g.label)).toEqual(["Đề & câu hỏi", "Lớp & học sinh", "Báo cáo", "Cài đặt"]);
    expect(groupsFor("teacher").flatMap((g) => g.items.map((i) => i.href))).not.toContain("/org/settings/ingestion");
    expect(groupsFor("super_admin").map((g) => g.label)).toEqual(["Cài đặt", "Hệ thống"]);
    expect(groupsFor("student").flatMap((g) => g.items.map((i) => i.href))).toEqual(["/home", "/me/stats"]);
    expect(homeFor("teacher")).toBe("/org/review");
  });

  it("marks the current page", () => {
    render(<Sidebar me={me("org_admin")} pathname="/org/bank" />);
    expect(screen.getByRole("link", { name: "Ngân hàng câu hỏi" })).toHaveAttribute("aria-current", "page");
  });

  it("opens a drawer on phones", () => {
    render(<AppShell me={me("teacher")}><p>nội dung</p></AppShell>);
    fireEvent.click(screen.getByRole("button", { name: "Mở menu" }));
    const drawer = screen.getByRole("dialog", { name: "Menu" });
    expect(within(drawer).getByRole("link", { name: "Đề thi & giao bài" })).toBeInTheDocument();
  });
});
