import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { UserTable } from "@/components/org/UserTable";
import { rolesManagedBy, UserCreateForm } from "@/components/org/UserForm";
import type { User } from "@/lib/types";
import { mockFetch, route } from "./helpers";

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

  it("row actions: edit, reset, deactivate (not for myself)", async () => {
    const onReset = vi.fn();
    const onToggle = vi.fn();
    render(
      <UserTable
        users={[user({ id: "me", username: "admin", role: "org_admin" }), user({ id: "s", username: "hs01", is_active: false })]}
        meId="me"
        className={() => ""}
        onEdit={() => {}}
        onReset={onReset}
        onToggle={onToggle}
      />,
    );
    expect(screen.getByTestId("user-admin")).not.toHaveTextContent("Khóa");
    const row = screen.getByTestId("user-hs01");
    expect(row).toHaveTextContent("Đã khóa");
    await userEvent.click(screen.getAllByRole("button", { name: "Mở khóa" })[0]);
    expect(onToggle).toHaveBeenCalled();
    await userEvent.click(screen.getAllByRole("button", { name: "Đặt lại mật khẩu" })[1]);
    expect(onReset).toHaveBeenCalledWith(expect.objectContaining({ username: "hs01" }));
  });
});
