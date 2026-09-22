import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MeProvider } from "@/app/(app)/AppShell";
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
