import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OrgCreateForm } from "@/components/admin/OrgForm";
import { OrgTable } from "@/components/admin/OrgTable";
import type { Org } from "@/lib/types";
import { mockFetch, route } from "./helpers";

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
    mockFetch(route("POST", "/api/admin/orgs", { error: { code: "conflict", message: "Mã tổ chức đã tồn tại", fields: { code: "Mã tổ chức đã tồn tại" } } }, 409));
    render(<OrgCreateForm onDone={() => {}} />);
    await userEvent.type(screen.getByLabelText(/Mã tổ chức/), "TRUNGTAMA");
    await userEvent.type(screen.getByLabelText("Tên tổ chức"), "X");
    await userEvent.click(screen.getByRole("button", { name: "Tạo tổ chức" }));
    expect(await screen.findByText("Mã tổ chức đã tồn tại")).toBeInTheDocument();
  });

  it("offers suspend/delete for tenants but not for the system org", () => {
    const onAction = vi.fn();
    render(<OrgTable orgs={[org({ code: "system", is_system: true }), org({ code: "trungtama" })]} onEdit={() => {}} onAction={onAction} />);
    const sys = screen.getByTestId("org-system");
    expect(sys).not.toHaveTextContent("Khóa");
    const tenant = screen.getByTestId("org-trungtama");
    expect(tenant).toHaveTextContent("Khóa");
    expect(tenant).toHaveTextContent("Xóa");
  });
});
