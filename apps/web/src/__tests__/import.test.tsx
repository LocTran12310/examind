import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ImportWizard } from "@/components/org/ImportWizard";
import { mockFetch, route } from "./helpers";

const row = (n: number, errors: string[] = []) => ({
  row: n,
  full_name: n === 7 ? "" : `HS ${n}`,
  username: `hs${n}`,
  role: "student",
  class: "10A1",
  errors,
  generated_username: true,
});

afterEach(() => vi.unstubAllGlobals());

describe("import wizard", () => {
  it("lists row errors and blocks commit until errors are skipped", async () => {
    const fetchMock = mockFetch(
      route("POST", "/api/users/import/preview", { rows: [row(2), row(7, ["Thiếu họ tên"])], valid_count: 1, error_count: 1 }),
      route("POST", "/api/users/import/commit", { created: [{ user_id: "1", username: "hs2", full_name: "HS 2", temp_password: "Pw23456789" }] }, 201),
    );
    render(<ImportWizard orgCode="trungtama" />);
    fireEvent.change(screen.getByTestId("file"), { target: { files: [new File(["x"], "a.csv")] } });
    expect(await screen.findByTestId("row-7")).toHaveTextContent("Thiếu họ tên");
    const commit = screen.getByRole("button", { name: /Tạo \d+ tài khoản/ });
    expect(commit).toBeDisabled();
    await userEvent.click(screen.getByLabelText("Bỏ qua các dòng lỗi"));
    await userEvent.click(screen.getByRole("button", { name: "Tạo 1 tài khoản" }));
    expect(await screen.findByText("Đã tạo 1 tài khoản.")).toBeInTheDocument();
    const body = JSON.parse(String(fetchMock.mock.calls.at(-1)?.[1]?.body));
    expect(body.rows.map((r: { row: number }) => r.row)).toEqual([2]);
  });

  it("downloads the credentials CSV", async () => {
    mockFetch(
      route("POST", "/api/users/import/preview", { rows: [row(2)], valid_count: 1, error_count: 0 }),
      route("POST", "/api/users/import/commit", { created: [{ user_id: "1", username: "hs2", full_name: "HS 2", temp_password: "Pw23456789" }] }, 201),
    );
    const createObjectURL = vi.fn(() => "blob:x");
    vi.stubGlobal("URL", Object.assign(URL, { createObjectURL, revokeObjectURL: vi.fn() }));
    render(<ImportWizard orgCode="trungtama" />);
    fireEvent.change(screen.getByTestId("file"), { target: { files: [new File(["x"], "a.csv")] } });
    await userEvent.click(await screen.findByRole("button", { name: "Tạo 1 tài khoản" }));
    await userEvent.click(await screen.findByRole("button", { name: /Tải danh sách mật khẩu/ }));
    expect(createObjectURL).toHaveBeenCalled();
    expect(await screen.findByText("Đã tải file.")).toBeInTheDocument();
  });
});
