import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MeProvider } from "@/app/(app)/AppShell";
import ClassesPage from "@/app/(app)/org/classes/page";
import SchoolYearsPage from "@/app/(app)/org/school-years/page";
import { HistoryPanel } from "@/components/app/HistoryPanel";
import { ThemeProvider } from "@/components/app/ThemeProvider";
import { YearProvider } from "@/components/app/YearContext";
import { YearSwitcher } from "@/components/app/YearSwitcher";
import type { SchoolYear } from "@/lib/types";
import { lastQuery, me, mockFetch, page, route } from "./helpers";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const year = (code: string, status: SchoolYear["status"], id = code): SchoolYear => ({
  id, code, name: `Năm học ${code}`, start_date: `${code.slice(0, 4)}-09-05`, end_date: `${code.slice(5)}-05-31`, status, class_count: 2,
  terms: [
    { code: "hk1", name: "Học kỳ 1", start_date: `${code.slice(0, 4)}-09-05`, end_date: `${code.slice(5)}-01-15` },
    { code: "hk2", name: "Học kỳ 2", start_date: `${code.slice(5)}-01-16`, end_date: `${code.slice(5)}-05-31` },
  ],
});
const years = page([year("2027-2028", "planning", "y2"), year("2026-2027", "active", "y1")]);

function wrap(ui: React.ReactNode, role: "org_admin" | "teacher" = "org_admin") {
  return render(
    <ThemeProvider>
      <MeProvider value={me(role)}>
        <YearProvider me={me(role)}>{ui}</YearProvider>
      </MeProvider>
    </ThemeProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
  setUrl("/org/classes");
});

describe("school years", () => {
  it("the header selector defaults to the active year, remembers the choice per org and scopes the class list", async () => {
    const fetch = mockFetch(route("GET", /^\/api\/school-years\?/, years), route("GET", /^\/api\/classes\?/, page([])));
    const u = userEvent.setup();
    wrap(
      <>
        <YearSwitcher />
        <ClassesPage />
      </>,
    );
    const sel = await screen.findByRole("combobox", { name: "Chọn năm học" });
    expect(sel).toHaveTextContent("2026-2027");
    await waitFor(() => expect(lastQuery(fetch, "/classes").get("school_year_id")).toBe("y1"));
    await u.click(sel);
    await u.click(await screen.findByRole("option", { name: /2027-2028/ }));
    await waitFor(() => expect(lastQuery(fetch, "/classes").get("school_year_id")).toBe("y2"));
    expect(localStorage.getItem("examind.year.o1")).toBe("y2");
  });

  it("activating a year asks first; close/reopen follow the status", async () => {
    setUrl("/org/school-years");
    const fetch = mockFetch(route("GET", /^\/api\/school-years\?/, years), route("POST", "/api/school-years/y2/activate", year("2027-2028", "active", "y2")));
    const u = userEvent.setup();
    wrap(<SchoolYearsPage />);
    const row = (await screen.findByText("2027-2028")).closest("tr")!;
    expect(row).toHaveTextContent("Chuẩn bị");
    expect(row).toHaveTextContent("Học kỳ 1");
    await u.click(within(row).getByRole("checkbox"));
    expect(screen.getByRole("button", { name: "Mở lại" })).toBeDisabled();
    await u.click(screen.getByRole("button", { name: "Đặt làm năm đang học" }));
    const dlg = await screen.findByRole("alertdialog");
    expect(dlg).toHaveTextContent("Năm đang học hiện tại sẽ được khóa");
    await u.click(within(dlg).getByRole("button", { name: "Xác nhận" }));
    await waitFor(() => expect(fetch.mock.calls.some(([url]) => url === "/api/school-years/y2/activate")).toBe(true));
  });

  it("history lists audit entries with the closed-year flag", async () => {
    setUrl("/org/school-years");
    const fetch = mockFetch(
      route("GET", /^\/api\/audit\?/, page([{ id: "a1", created_at: "2026-09-22T10:00:00Z", organization_id: "o1", organization_code: "trungtama", actor_id: "u", actor_name: "Cô Lan", action: "class.update", target_type: "class", target_id: "c1", data: { closed_year: true, changes: { name: ["10A1", "10A1-CLC"] } } }])),
    );
    render(<HistoryPanel targetId="c1" />);
    const row = (await screen.findByText("Sửa lớp")).closest("tr")!;
    expect(row).toHaveTextContent("năm đã khóa");
    expect(row).toHaveTextContent("name: 10A1 → 10A1-CLC");
    expect(row).toHaveTextContent("Cô Lan");
    expect(lastQuery(fetch, "/audit").get("target_id")).toBe("c1");
  });
});
