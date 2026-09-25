import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MeProvider } from "@/hooks/common/use-me";
import ReportsPage from "@/app/(app)/org/reports/page";
import { lastBody, lastQuery, me, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";
import { useYearStore } from "@/stores/common/year.store";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const year = { id: "y1", code: "2026-2027", name: "Năm học 2026-2027", start_date: "2026-09-05", end_date: "2027-05-31", status: "active", class_count: 1, terms: [] };

beforeEach(() => {
  localStorage.clear();
  useYearStore.setState({ chosen: {} });
  setUrl("/org/reports");
});

describe("reports by year and term", () => {
  it("defaults to the header year and filters by HK; a class replaces the year filter", async () => {
    const fetch = mockFetch(
      route("POST", "/api/school-years/search", searchPage([year])),
      route("POST", "/api/classes/search", searchPage([{ id: "c1", name: "10A1", grade: 10, school_year: "2026-2027", school_year_id: "y1", member_count: 1, created_at: "" }])),
      route("GET", /^\/api\/stats\/topics/, []),
    );
    const u = userEvent.setup();
    render(
      <MeProvider value={me("teacher")}>
        <ReportsPage />
      </MeProvider>,
    );
    await waitFor(() => expect(lastQuery(fetch, "/stats/topics").get("school_year_id")).toBe("y1"));
    expect(lastBody(fetch, "/classes/search").school_year_id).toBe("y1");
    await u.click(screen.getByRole("combobox", { name: "Học kỳ" }));
    await u.click(await screen.findByRole("option", { name: "Học kỳ 2" }));
    await waitFor(() => expect(lastQuery(fetch, "/stats/topics").get("term_code")).toBe("hk2"));
    await u.click(screen.getByRole("combobox", { name: "Lớp" }));
    await u.click(await screen.findByRole("option", { name: /10A1/ }));
    await waitFor(() => {
      const q = lastQuery(fetch, "/stats/topics");
      expect([q.get("class_id"), q.get("school_year_id"), q.get("term_code")]).toEqual(["c1", null, "hk2"]);
    });
  });
});

describe("báo cáo khi trung tâm dạy nhiều môn", () => {
  const taxonomy = { subjects: [{ id: "toan", code: "toan", name: "Toán" }, { id: "ly", code: "ly", name: "Vật lí" }], grades: [], semesters: [] };
  const stat = (id: string, name: string, path: string, subject_id: string) => ({
    id, parent_id: null, name, path, depth: 1, level_kind: "strand", subject_id,
    points: 6, max_points: 10, answered: 10, ratio: 0.6,
  });

  it("mặc định vẫn là mọi môn, và chọn một môn mới hẹp lại", async () => {
    // AC-05. Đổi mặc định sang một môn là đổi NGHĨA của con số trang này mà không ai được báo: "62%" hôm nay là
    // của cả trung tâm, ngày mai là của Toán, và màn hình không nói gì. Nên mặc định phải không gửi subject_id.
    const fetch = mockFetch(
      route("POST", "/api/school-years/search", searchPage([year])),
      route("POST", "/api/classes/search", searchPage([])),
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", /^\/api\/stats\/topics/, [stat("ds", "Đại số", "ds", "toan")]),
    );
    const u = userEvent.setup();
    render(<MeProvider value={me("teacher")}><ReportsPage /></MeProvider>);

    await waitFor(() => expect(lastQuery(fetch, "/stats/topics").get("school_year_id")).toBe("y1"));
    expect(lastQuery(fetch, "/stats/topics").get("subject_id")).toBeNull();

    await u.click(screen.getByRole("combobox", { name: "Môn" }));
    await u.click(await screen.findByRole("option", { name: "Vật lí" }));
    await waitFor(() => expect(lastQuery(fetch, "/stats/topics").get("subject_id")).toBe("ly"));
  });

  it("ở mọi môn, các mạch nhóm dưới môn của chúng", async () => {
    // AC-06. Phẳng thì đọc được khi một môn và không đọc được khi hai — đúng điều này sinh ra để sửa.
    mockFetch(
      route("POST", "/api/school-years/search", searchPage([year])),
      route("POST", "/api/classes/search", searchPage([])),
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", /^\/api\/stats\/topics/, [stat("ds", "Đại số", "ds", "toan"), stat("co", "Cơ học", "co", "ly")]),
    );
    render(<MeProvider value={me("teacher")}><ReportsPage /></MeProvider>);

    expect(await screen.findByTestId("subject-Toán")).toHaveTextContent("Đại số");
    expect(screen.getByTestId("subject-Vật lí")).toHaveTextContent("Cơ học");
  });

  it("một môn thì không có tiêu đề môn nào cả", async () => {
    // Trung tâm dạy một môn nhìn y như trước: một tiêu đề lặp lại trên mọi hàng chỉ là tiếng ồn.
    mockFetch(
      route("POST", "/api/school-years/search", searchPage([year])),
      route("POST", "/api/classes/search", searchPage([])),
      route("GET", "/api/taxonomy", { ...taxonomy, subjects: [taxonomy.subjects[0]] }),
      route("GET", /^\/api\/stats\/topics/, [stat("ds", "Đại số", "ds", "toan")]),
    );
    render(<MeProvider value={me("teacher")}><ReportsPage /></MeProvider>);

    expect(await screen.findByTestId("topic-stats")).toHaveTextContent("Đại số");
    expect(screen.queryByTestId("subject-Toán")).not.toBeInTheDocument();
  });
});
