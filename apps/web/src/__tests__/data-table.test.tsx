import type { ColumnDef } from "@tanstack/react-table";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DataTable } from "@/components/data-table/DataTable";
import { mockFetch } from "./helpers";
import { currentUrl, router, searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

type Row = { id: string; name: string; role: string };
const cols: ColumnDef<Row, unknown>[] = [
  { accessorKey: "name", header: "Họ tên", meta: { filter: { kind: "text" }, sort: "full_name" } },
  { accessorKey: "role", header: "Vai trò", meta: { filter: { kind: "select", options: [{ value: "student", label: "Học sinh" }, { value: "teacher", label: "Giáo viên" }] } } },
];
const rows = (n: number, from = 0): Row[] => Array.from({ length: n }, (_, i) => ({ id: `r${from + i}`, name: `Người ${from + i}`, role: "student" }));

function serve(total = 45) {
  return mockFetch((url) => {
    if (!url.startsWith("/api/people")) return undefined;
    const q = new URL(url, "http://x").searchParams;
    const page = Number(q.get("page")), size = Number(q.get("page_size"));
    return { body: { items: rows(Math.max(0, Math.min(size, total - (page - 1) * size)), (page - 1) * size), total, page, page_size: size } };
  });
}
const requested = (fetch: ReturnType<typeof serve>) => new URL(String(fetch.mock.calls.at(-1)![0]), "http://x").searchParams;

describe("DataTable", () => {
  beforeEach(() => {
    setUrl("/org/people");
    router.push.mockClear();
    router.replace.mockClear();
  });

  it("types into a column filter → after the debounce the URL and the server request carry it", async () => {
    const fetch = serve();
    const user = userEvent.setup();
    render(<DataTable path="/people" columns={cols} getRowId={(r) => r.id} />);
    await screen.findByText("Người 0");
    await user.type(screen.getByRole("textbox", { name: "Lọc Họ tên" }), "bùi");
    expect(searchOf().get("full_name")).toBeNull(); // not before the pause
    await waitFor(() => expect(searchOf().get("name")).toBe("bùi"), { timeout: 1500 });
    await waitFor(() => expect(requested(fetch).get("name")).toBe("bùi"));
    expect(router.replace).toHaveBeenCalled();
  });

  it("opens a link with state: the first request already has the filters, sort and page", async () => {
    setUrl("/org/people?name=an&role=teacher&sort=-full_name&page=2&page_size=50");
    const fetch = serve(120);
    render(<DataTable path="/people" columns={cols} getRowId={(r) => r.id} />);
    await screen.findByText("Người 50");
    expect(fetch).toHaveBeenCalledTimes(1);
    const q = requested(fetch);
    expect([q.get("name"), q.get("role"), q.get("sort"), q.get("page"), q.get("page_size")]).toEqual(["an", "teacher", "-full_name", "2", "50"]);
    expect(screen.getByRole("textbox", { name: "Lọc Họ tên" })).toHaveValue("an");
    expect(screen.getByRole("combobox", { name: "Lọc Vai trò" })).toHaveTextContent("Giáo viên");
    expect(screen.getByRole("columnheader", { name: /Họ tên/ })).toHaveAttribute("aria-sort", "descending");
  });

  it("pages on the server and shows the footer range", async () => {
    const fetch = serve(45);
    const user = userEvent.setup();
    render(<DataTable path="/people" columns={cols} getRowId={(r) => r.id} />);
    await screen.findByText("Người 0");
    expect(screen.getByText("Hiển thị 1–20 trên 45 kết quả")).toBeInTheDocument();
    expect(screen.getByText("trên 3")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Trang cuối" }));
    await screen.findByText("Người 40");
    expect(currentUrl()).toBe("/org/people?page=3");
    expect(router.push).toHaveBeenCalled();
    expect(requested(fetch).get("page")).toBe("3");
    expect(screen.getByText("Hiển thị 41–45 trên 45 kết quả")).toBeInTheDocument();
    const pageBox = screen.getByRole("textbox", { name: "Số trang" });
    await user.clear(pageBox);
    await user.type(pageBox, "2{Enter}");
    await waitFor(() => expect(searchOf().get("page")).toBe("2"));
  });

  it("filtering resets to page 1; sort cycles asc → desc → none", async () => {
    setUrl("/org/people?page=3");
    serve(45);
    const user = userEvent.setup();
    render(<DataTable path="/people" columns={cols} getRowId={(r) => r.id} />);
    await screen.findByText("Người 40");
    await user.click(screen.getByRole("combobox", { name: "Lọc Vai trò" }));
    await user.click(await screen.findByRole("option", { name: "Giáo viên" }));
    expect(currentUrl()).toBe("/org/people?role=teacher");
    const sortBtn = within(screen.getByRole("columnheader", { name: /Họ tên/ })).getByRole("button");
    await user.click(sortBtn);
    expect(searchOf().get("sort")).toBe("full_name");
    await user.click(sortBtn);
    expect(searchOf().get("sort")).toBe("-full_name");
    await user.click(sortBtn);
    expect(searchOf().get("sort")).toBeNull();
  });

  it("selection drives Sửa/Xóa; Xóa asks to confirm; Nạp reloads", async () => {
    const fetch = serve(3);
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    const user = userEvent.setup();
    render(<DataTable path="/people" columns={cols} getRowId={(r) => r.id} onAdd={() => {}} onEdit={onEdit} onDelete={onDelete} />);
    await screen.findByText("Người 0");
    const edit = screen.getByRole("button", { name: "Sửa" });
    const del = screen.getByRole("button", { name: "Xóa" });
    expect(edit).toBeDisabled();
    expect(del).toBeDisabled();
    const boxes = screen.getAllByRole("checkbox", { name: "Chọn dòng" });
    await user.click(boxes[0]);
    expect(edit).toBeEnabled();
    await user.click(boxes[1]);
    expect(edit).toBeDisabled();
    expect(del).toBeEnabled();
    await user.click(del);
    const dialog = await screen.findByRole("alertdialog");
    expect(dialog).toHaveTextContent("Xóa 2 dòng đã chọn?");
    expect(onDelete).not.toHaveBeenCalled();
    const calls = fetch.mock.calls.length;
    await user.click(within(dialog).getByRole("button", { name: "Xóa" }));
    await waitFor(() => expect(onDelete).toHaveBeenCalledWith([expect.objectContaining({ id: "r0" }), expect.objectContaining({ id: "r1" })]));
    await waitFor(() => expect(fetch.mock.calls.length).toBeGreaterThan(calls));
    const before = fetch.mock.calls.length;
    await user.click(screen.getByRole("button", { name: "Nạp" }));
    await waitFor(() => expect(fetch.mock.calls.length).toBe(before + 1));
  });

  it("URL change from outside (Back) updates the inputs", async () => {
    serve(10);
    render(<DataTable path="/people" columns={cols} getRowId={(r) => r.id} />);
    await screen.findByText("Người 0");
    act(() => setUrl("/org/people?name=lan"));
    await waitFor(() => expect(screen.getByRole("textbox", { name: "Lọc Họ tên" })).toHaveValue("lan"));
  });
});
