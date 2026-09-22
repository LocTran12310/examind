import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import OrgsPage from "@/app/(app)/admin/orgs/page";
import { OrgCreateForm } from "@/components/page-components/Orgs/OrgForm/OrgForm";
import type { Org } from "@/interfaces/org.interface";
import { lastBody, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";
import { router, searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const org = (o: Partial<Org>): Org => ({
  id: o.code ?? "id",
  code: "trungtama",
  name: "Trung tâm A",
  status: "active",
  is_system: false,
  user_count: 1,
  created_at: "2026-09-21T00:00:00Z",
  deleted_at: null,
  ...o,
});

beforeEach(() => setUrl("/admin/orgs"));
afterEach(() => vi.unstubAllGlobals());

describe("admin orgs", () => {
  it("shows the temporary password once after creation", async () => {
    mockFetch(route("POST", "/api/admin/orgs", { org: org({}), admin: { username: "admin", temp_password: "Abc234defg" } }, 201));
    render(<OrgCreateForm onDone={() => {}} />);
    await userEvent.type(screen.getByLabelText(/Mã tổ chức/), "TrungtamA");
    await userEvent.type(screen.getByLabelText("Tên tổ chức"), "Trung tâm A");
    await userEvent.click(screen.getByRole("button", { name: "Tạo tổ chức" }));
    expect(await screen.findByTestId("temp-cred")).toHaveTextContent("trungtama / admin / Abc234defg");
  });

  it("renders field errors", async () => {
    mockFetch(route("POST", "/api/admin/orgs", { code: "conflict", message: "Mã tổ chức đã tồn tại", details: { fields: { code: "Mã tổ chức đã tồn tại" } } }, 409));
    render(<OrgCreateForm onDone={() => {}} />);
    await userEvent.type(screen.getByLabelText(/Mã tổ chức/), "TRUNGTAMA");
    await userEvent.type(screen.getByLabelText("Tên tổ chức"), "X");
    await userEvent.click(screen.getByRole("button", { name: "Tạo tổ chức" }));
    expect(await screen.findByText("Mã tổ chức đã tồn tại")).toBeInTheDocument();
  });

  it("suspends a tenant after confirmation but never the system org", async () => {
    const fetch = mockFetch(
      route("POST", "/api/admin/orgs/search", searchPage([org({ code: "system", name: "Examind", is_system: true }), org({ code: "trungtama" })])),
      route("POST", "/api/admin/orgs/trungtama/suspend", org({ status: "suspended" })),
    );
    const u = userEvent.setup();
    render(<OrgsPage />);
    await screen.findByText("Examind");
    const [sys, tenant] = screen.getAllByRole("checkbox", { name: "Chọn dòng" });
    await u.click(sys);
    expect(screen.getByRole("button", { name: "Khóa" })).toBeDisabled();
    await u.click(sys);
    await u.click(tenant);
    await u.click(screen.getByRole("button", { name: "Khóa" }));
    await u.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xác nhận" }));
    await waitFor(() => expect(fetch.mock.calls.some(([url]) => url === "/api/admin/orgs/trungtama/suspend")).toBe(true));
  });

  it("the deleted switch and the code filter go to the server", async () => {
    const fetch = mockFetch(route("POST", "/api/admin/orgs/search", searchPage([org({})])));
    const u = userEvent.setup();
    render(<OrgsPage />);
    await screen.findByText("Trung tâm A");
    await u.click(screen.getByRole("switch", { name: "Hiện tổ chức đã xóa" }));
    await waitFor(() => expect(lastBody(fetch, "/admin/orgs/search").include_deleted).toBe(true));
    await u.type(screen.getByRole("textbox", { name: "Lọc Mã" }), "tt");
    await waitFor(() => expect(lastBody(fetch, "/admin/orgs/search").filters).toEqual({ code: { value: "tt" } }), { timeout: 1500 });
    expect(searchOf().get("include_deleted")).toBe("true");
  });

  it("'Vào tổ chức' switches into the selected org through the router, with a fresh cache", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign });
    const fetch = mockFetch(route("POST", "/api/admin/orgs/search", searchPage([org({ id: "a1", code: "trungtama" })])), route("POST", "/api/auth/switch-org", {}));
    const u = userEvent.setup();
    const { client } = render(<OrgsPage />);
    const clear = vi.spyOn(client, "clear");
    await u.click(await screen.findByRole("checkbox", { name: "Chọn dòng" }));
    await u.click(screen.getByRole("button", { name: "Vào tổ chức" }));
    await waitFor(() => expect(router.push).toHaveBeenCalledWith("/org/users"));
    expect(router.refresh).toHaveBeenCalled();
    expect(clear).toHaveBeenCalled();
    expect(assign).not.toHaveBeenCalled();
    expect(JSON.parse(String((fetch.mock.calls.find(([url]) => url === "/api/auth/switch-org")?.[1] as RequestInit).body))).toEqual({ org_id: "a1" });
  });
});
