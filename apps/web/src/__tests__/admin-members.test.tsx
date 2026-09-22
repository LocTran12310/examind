import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AccountsPage from "@/app/(app)/admin/users/page";
import { MembershipTable } from "@/components/admin/MembershipTable";
import type { Membership } from "@/lib/types";
import { mockFetch, page, route } from "./helpers";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const mem = (o: Partial<Membership>): Membership => ({
  user_id: "u1", username: "lan", full_name: "Cô Lan", home_org_code: "tta", org_id: "a", org_code: "tta", org_name: "Trung tâm A",
  role: "teacher", is_active: true, is_home: true, ...o,
});
const body = (fetch: ReturnType<typeof mockFetch>, url: string, method = "POST") =>
  JSON.parse(String((fetch.mock.calls.find(([u, i]) => u === url && ((i as RequestInit)?.method ?? "GET") === method)?.[1] as RequestInit).body));

beforeEach(() => setUrl("/admin/orgs"));

describe("org ↔ user assignment", () => {
  it("org side: add an account by home org code + username, change a role", async () => {
    const fetch = mockFetch(
      route("GET", /^\/api\/admin\/orgs\/b\/members\?/, page([mem({ org_id: "b", org_code: "ttb", org_name: "Trung tâm B", is_home: false })])),
      route("POST", "/api/admin/orgs/b/members", mem({ org_id: "b", is_home: false }), 201),
      route("PATCH", "/api/admin/orgs/b/members/u1", mem({ org_id: "b", role: "org_admin", is_home: false })),
    );
    const u = userEvent.setup();
    render(<MembershipTable side={{ kind: "org", orgId: "b", orgName: "Trung tâm B" }} />);
    const row = (await screen.findByText("Cô Lan")).closest("tr")!;
    expect(row).toHaveTextContent("tta/lan");
    await u.click(screen.getByRole("button", { name: "Thêm tài khoản" }));
    const dlg = await screen.findByRole("dialog");
    await u.type(within(dlg).getByLabelText("Mã tổ chức gốc"), "tta");
    await u.type(within(dlg).getByLabelText("Tên đăng nhập"), "lan");
    await u.click(within(dlg).getByRole("button", { name: "Thêm" }));
    await waitFor(() => expect(body(fetch, "/api/admin/orgs/b/members")).toEqual({ org_code: "tta", username: "lan", role: "teacher" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    await u.click(within(screen.getByText("Cô Lan").closest("tr")!).getByRole("checkbox"));
    await u.click(screen.getByRole("button", { name: /Đổi vai trò/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Quản trị trung tâm" }));
    await waitFor(() => expect(body(fetch, "/api/admin/orgs/b/members/u1", "PATCH")).toEqual({ role: "org_admin" }));
  });

  it("user side: accounts list → organisations panel → add an org; the home org cannot be locked", async () => {
    setUrl("/admin/users");
    const fetch = mockFetch(
      route("GET", /^\/api\/admin\/users\?/, page([{ id: "u1", username: "lan", full_name: "Cô Lan", home_org_code: "tta", home_org_name: "Trung tâm A", is_active: true, org_count: 1 }])),
      route("GET", /^\/api\/admin\/users\/u1\/memberships\?/, page([mem({})])),
      route("GET", /^\/api\/admin\/orgs\?/, page([{ id: "b", code: "ttb", name: "Trung tâm B", status: "active", is_system: false, user_count: 3, created_at: "", deleted_at: null }])),
      route("POST", "/api/admin/users/u1/memberships", mem({ org_id: "b", is_home: false }), 201),
    );
    const u = userEvent.setup();
    render(<AccountsPage />);
    await u.click(await screen.findByText("Cô Lan"));
    await screen.findByText("Tổ chức của Cô Lan");
    const home = (await screen.findAllByText("Trung tâm A (tta)")).at(-1)!.closest("tr")!; // the panel's row, not the accounts list
    expect(home).toHaveTextContent("Tổ chức gốc");
    await u.click(within(home).getByRole("checkbox"));
    expect(screen.getByRole("button", { name: "Khóa" })).toBeDisabled();
    await u.click(screen.getByRole("button", { name: "Thêm vào tổ chức" }));
    const dlg = await screen.findByRole("dialog");
    await u.click(within(dlg).getByRole("combobox", { name: "Tổ chức" }));
    await u.click(await screen.findByRole("option", { name: "Trung tâm B (ttb)" }));
    await u.click(within(dlg).getByRole("button", { name: "Thêm" }));
    await waitFor(() => expect(body(fetch, "/api/admin/users/u1/memberships")).toEqual({ org_id: "b", role: "teacher" }));
  });
});
