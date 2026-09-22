import type { ColumnDef } from "@tanstack/react-table";
import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DataTable as SearchTable, type DataTableProps } from "@/components/common/DataTable/DataTable";
import type { SearchBody } from "@/dtos/search.dto";
import { useSearchQuery } from "@/hooks/react-query/use-search-query";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";
import { mockFetch, renderWithQuery as render } from "./helpers";
import { currentUrl, router, searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

type Row = { id: string; name: string; role: string };
const cols: ColumnDef<Row, unknown>[] = [
  { accessorKey: "name", header: "Họ tên", meta: { filter: { kind: "text" }, sort: "full_name" } },
  { accessorKey: "role", header: "Vai trò", meta: { filter: { kind: "select", options: [{ value: "student", label: "Học sinh" }, { value: "teacher", label: "Giáo viên" }] } } },
];
const rows = (n: number, from = 0): Row[] => Array.from({ length: n }, (_, i) => ({ id: `r${from + i}`, name: `Người ${from + i}`, role: "student" }));

// a resource on the search contract: POST /people/search {page, limit, sort, filters} → {data, total, page, limit}
const usePeopleSearchQuery = (body: SearchBody, options?: RowsQueryOptions<Row>) =>
  useSearchQuery(["people", body], (b: SearchBody) => http<SearchPage<Row>>("/people/search", { body: b }), body, options);
const DataTable = (props: Omit<DataTableProps<Row>, "useRows">) => <SearchTable<Row> useRows={usePeopleSearchQuery} {...props} />;

function serve(total = 45) {
  return mockFetch((url, init) => {
    if (url !== "/api/people/search") return undefined;
    const { page, limit } = JSON.parse(String(init?.body)) as SearchBody;
    return { body: { data: rows(Math.max(0, Math.min(limit, total - (page - 1) * limit)), (page - 1) * limit), total, page, limit } };
  });
}
const requested = (fetch: ReturnType<typeof serve>) => JSON.parse(String(fetch.mock.calls.at(-1)![1]?.body)) as SearchBody;

describe("DataTable", () => {
  beforeEach(() => {
    setUrl("/org/people");
    router.push.mockClear();
    router.replace.mockClear();
  });

  it("operators per column text * = + - !, dates = < ≤ > ≥ or a range (ui-standards AC-02)", async () => {
    const fetch = serve();
    const u = userEvent.setup();
    const withDate: ColumnDef<Row, unknown>[] = [...cols, { id: "created_at", header: "Tạo lúc", meta: { filter: { kind: "date" } } }];
    render(<DataTable columns={withDate} getRowId={(r) => r.id} />);
    await screen.findByText("Người 0");
    await u.click(screen.getByRole("button", { name: "Kiểu lọc Họ tên: Chứa" }));
    expect(screen.getByText("Chọn kiểu lọc")).toBeInTheDocument();
    await u.click(screen.getByRole("menuitemradio", { name: /Bắt đầu bằng/ }));
    expect(searchOf().get("name_op")).toBe("+");
    expect(screen.getByRole("button", { name: "Kiểu lọc Họ tên: Bắt đầu bằng" })).toHaveTextContent("+");
    // dates: a range by default; ≥ turns it into one day with the operator
    expect(screen.getByLabelText("Tạo lúc trong khoảng")).toBeInTheDocument();
    // the shadcn date picker (Popover + Calendar), not a native date input
    await u.click(screen.getByLabelText("Tạo lúc trong khoảng"));
    await u.click(within(await screen.findByRole("grid")).getByRole("button", { name: /\b15\b/ }));
    const day = searchOf().get("created_at_from");
    expect(day).toMatch(/^\d{4}-\d{2}-15$/);
    await u.click(screen.getByRole("button", { name: "Kiểu lọc Tạo lúc: Trong khoảng" }));
    await u.click(screen.getByRole("menuitemradio", { name: /Lớn hơn hoặc bằng/ }));
    expect([searchOf().get("created_at"), searchOf().get("created_at_op"), searchOf().get("created_at_from")]).toEqual([day, ">=", null]);
    await waitFor(() => expect(requested(fetch).filters?.created_at?.operator).toBe(">="));
  });

  it("separates columns and tints every other row (ui-polish AC-02)", async () => {
    serve(3);
    render(<DataTable columns={cols} getRowId={(r) => r.id} />);
    const cell = await screen.findByText("Người 1");
    expect(cell.closest("td")).toHaveClass("border-r");
    expect(cell.closest("tr")).toHaveClass("even:bg-muted/40");
    expect(screen.getByRole("columnheader", { name: /Họ tên/ })).toHaveClass("border-r");
  });

  it("types into a column filter → after the debounce the URL and the server request carry it", async () => {
    const fetch = serve();
    const user = userEvent.setup();
    render(<DataTable columns={cols} getRowId={(r) => r.id} />);
    await screen.findByText("Người 0");
    await user.type(screen.getByRole("textbox", { name: "Lọc Họ tên" }), "bùi");
    expect(searchOf().get("full_name")).toBeNull(); // not before the pause
    await waitFor(() => expect(searchOf().get("name")).toBe("bùi"), { timeout: 1500 });
    await waitFor(() => expect(requested(fetch).filters?.name).toEqual({ value: "bùi" }));
    expect(router.replace).toHaveBeenCalled();
  });

  it("opens a link with state: the first request already has the filters, sort and page", async () => {
    setUrl("/org/people?name=an&role=teacher&sort=-full_name&page=2&page_size=50");
    const fetch = serve(120);
    render(<DataTable columns={cols} getRowId={(r) => r.id} />);
    await screen.findByText("Người 50");
    expect(fetch).toHaveBeenCalledTimes(1);
    const b = requested(fetch);
    expect([b.filters?.name, b.filters?.role, b.sort, b.page, b.limit]).toEqual([{ value: "an" }, { value: "teacher" }, [{ field: "full_name", desc: true }], 2, 50]);
    expect(screen.getByRole("textbox", { name: "Lọc Họ tên" })).toHaveValue("an");
    expect(screen.getByRole("combobox", { name: "Lọc Vai trò" })).toHaveTextContent("Giáo viên");
    expect(screen.getByRole("columnheader", { name: /Họ tên/ })).toHaveAttribute("aria-sort", "descending");
  });

  it("pages on the server and shows the footer range", async () => {
    const fetch = serve(45);
    const user = userEvent.setup();
    render(<DataTable columns={cols} getRowId={(r) => r.id} />);
    await screen.findByText("Người 0");
    expect(screen.getByText("Hiển thị 1–20 trên 45 kết quả")).toBeInTheDocument();
    expect(screen.getByText("trên 3")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Trang cuối" }));
    await screen.findByText("Người 40");
    expect(currentUrl()).toBe("/org/people?page=3");
    expect(router.push).toHaveBeenCalled();
    expect(requested(fetch).page).toBe(3);
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
    render(<DataTable columns={cols} getRowId={(r) => r.id} />);
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
    render(<DataTable columns={cols} getRowId={(r) => r.id} onAdd={() => {}} onEdit={onEdit} onDelete={onDelete} />);
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
    render(<DataTable columns={cols} getRowId={(r) => r.id} />);
    await screen.findByText("Người 0");
    act(() => setUrl("/org/people?name=lan"));
    await waitFor(() => expect(screen.getByRole("textbox", { name: "Lọc Họ tên" })).toHaveValue("lan"));
  });
});
