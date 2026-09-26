import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ImportWizard } from "@/components/page-components/UserImport/ImportWizard/ImportWizard";
import { mockFetch, renderWithQuery as render, route } from "./helpers";

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

const preview = () => route("POST", "/api/users/import/preview", { rows: [row(2)], valid_count: 1, error_count: 0 });
const csv = (name = "ds.csv", body = "x".repeat(2048)) => new File([body], name);

/** The drop zone can only be checked for behaviour here: jsdom has no layout, so "looks like a drop zone" is not testable. */
describe("file drop field on the import screen", () => {
  it("shows the chosen file with its size and previews it", async () => {
    mockFetch(preview());
    render(<ImportWizard orgCode="trungtama" />);
    fireEvent.change(screen.getByTestId("file"), { target: { files: [csv()] } });
    expect(await screen.findByTestId("row-2")).toBeInTheDocument();
    expect(screen.getByTestId("file-chosen")).toHaveTextContent("ds.csv");
    expect(screen.getByTestId("file-chosen")).toHaveTextContent("2,0 KB");
  });

  it("takes a file dropped on the zone", async () => {
    mockFetch(preview());
    render(<ImportWizard orgCode="trungtama" />);
    fireEvent.drop(screen.getByTestId("file-zone"), { dataTransfer: { files: [csv("keo-tha.csv")] } });
    expect(await screen.findByTestId("row-2")).toBeInTheDocument();
    expect(screen.getByTestId("file-chosen")).toHaveTextContent("keo-tha.csv");
  });

  it("refuses a wrong extension and sends nothing", async () => {
    const fetchMock = mockFetch(preview());
    render(<ImportWizard orgCode="trungtama" />);
    fireEvent.drop(screen.getByTestId("file-zone"), { dataTransfer: { files: [csv("danh-sach.pdf")] } });
    expect(await screen.findByText(/Chỉ nhận file \.csv, \.xlsx/)).toHaveTextContent("danh-sach.pdf");
    expect(screen.queryByTestId("file-chosen")).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("clears the file and the preview it produced", async () => {
    mockFetch(preview());
    render(<ImportWizard orgCode="trungtama" />);
    fireEvent.change(screen.getByTestId("file"), { target: { files: [csv()] } });
    await userEvent.click(await screen.findByRole("button", { name: "Bỏ file ds.csv" }));
    expect(screen.queryByTestId("file-chosen")).not.toBeInTheDocument();
    expect(screen.queryByTestId("row-2")).not.toBeInTheDocument();
  });

  it("links to the template kept in public/, whose header is the columns the importer reads", () => {
    mockFetch(preview());
    render(<ImportWizard orgCode="trungtama" />);
    const href = screen.getByRole("link", { name: /Tải file mẫu/ }).getAttribute("href")!;
    const template = readFileSync(path.join(process.cwd(), "public", href), "utf8").replace(/^﻿/, "").trim().split("\n");
    expect(template[0]).toBe("Họ tên,Tên đăng nhập,Vai trò,Lớp");
    expect(template.length).toBeGreaterThan(1);
    // the words the file shows are the words the hint names, and one row documents the `;` between two classes
    expect(screen.getByText(/Cột: Họ tên/)).toHaveTextContent("Tên đăng nhập, Vai trò, Lớp");
    expect(template.some((l) => l.includes("10A1; 11A2"))).toBe(true);
  });
});
