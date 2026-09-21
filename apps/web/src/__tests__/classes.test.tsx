import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ClassCreateForm, currentSchoolYear } from "@/components/org/ClassForms";
import { MemberManager } from "@/components/org/MemberManager";
import type { ClassDetail, User } from "@/lib/types";
import { mockFetch, route } from "./helpers";

const student = (username: string): User => ({
  id: username,
  username,
  full_name: username.toUpperCase(),
  email: null,
  role: "student",
  is_active: true,
  must_change_password: false,
  last_login_at: null,
  created_at: "",
  class_ids: [],
});

afterEach(() => vi.unstubAllGlobals());

describe("classes", () => {
  it("school year rolls over in August", () => {
    expect(currentSchoolYear(new Date(2026, 8, 1))).toBe("2026-2027");
    expect(currentSchoolYear(new Date(2027, 2, 1))).toBe("2026-2027");
  });

  it("creates a class", async () => {
    const f = mockFetch(route("POST", "/api/classes", { id: "c" }, 201));
    const onCreated = vi.fn();
    render(<ClassCreateForm onCreated={onCreated} />);
    await userEvent.type(screen.getByLabelText("Tên lớp"), "10A1");
    await userEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));
    await waitFor(() => expect(onCreated).toHaveBeenCalled());
    expect(JSON.parse(String(f.mock.calls[0][1]?.body)).name).toBe("10A1");
  });

  it("adds and removes members", async () => {
    const detail: ClassDetail = { id: "c1", name: "10A1", grade: 10, school_year: "2026-2027", member_count: 1, created_at: "", members: [student("hs01")] };
    const f = mockFetch(
      route("GET", /\/api\/users\?/, { items: [student("hs01"), student("hs02")], total: 2, page: 1, page_size: 20 }),
      route("POST", "/api/classes/c1/members", undefined, 204),
      route("DELETE", "/api/classes/c1/members/hs01", undefined, 204),
    );
    const onChange = vi.fn();
    render(<MemberManager detail={detail} onChange={onChange} />);
    await userEvent.type(screen.getByPlaceholderText("Tìm tên hoặc tên đăng nhập"), "hs");
    await userEvent.click(await screen.findByRole("button", { name: "Thêm" }));
    await waitFor(() => expect(onChange).toHaveBeenCalledTimes(1));
    expect(JSON.parse(String(f.mock.calls.find((c) => c[0] === "/api/classes/c1/members")?.[1]?.body)).user_ids).toEqual(["hs02"]);
    await userEvent.click(screen.getByRole("button", { name: "Xóa khỏi lớp" }));
    await waitFor(() => expect(onChange).toHaveBeenCalledTimes(2));
  });
});
