import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MeProvider } from "@/app/(app)/AppShell";
import ReviewPage from "@/app/(app)/org/review/page";
import type { ReviewDocument } from "@/interfaces/review.interface";
import type { User } from "@/interfaces/user.interface";
import { lastBody, me, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";
import { searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

export const reviewRow = (o: Partial<ReviewDocument> = {}): ReviewDocument => ({
  document: { id: "d1", filename: "de-kho.docx" } as ReviewDocument["document"],
  total: 8,
  counts: { auto_approved: 3, needs_review: 5, approved: 0, rejected: 0, duplicate: 0, flagged: 0 },
  spot_pending: 1,
  progress: 0.25,
  assigned_to: null,
  assigned_name: null,
  ...o,
});
const gv = { id: "u1", full_name: "Cô Lan" } as User;

const renderPage = (role: "teacher" | "org_admin") =>
  render(
    <MeProvider value={me(role)}>
      <ReviewPage />
    </MeProvider>,
  );

beforeEach(() => setUrl("/org/review"));

describe("review list", () => {
  it("shows counts, spot checks, progress and the pending link", async () => {
    mockFetch(route("POST", "/api/review/documents/search", searchPage([reviewRow()])));
    renderPage("teacher");
    const r = await screen.findByTestId("rev-de-kho.docx");
    const row = r.closest("tr")!;
    expect(row).toHaveTextContent("Tự duyệt 3");
    expect(row).toHaveTextContent("Cần xem 5");
    expect(row).toHaveTextContent("Kiểm tra ngẫu nhiên 1");
    expect(row).toHaveTextContent("25%");
    expect(screen.getByRole("link", { name: "Duyệt 6 câu" })).toHaveAttribute("href", "/org/review/d1");
  });

  it("'Của tôi' goes to the server and the URL", async () => {
    const fetch = mockFetch(route("POST", "/api/review/documents/search", searchPage([reviewRow()])));
    const u = userEvent.setup();
    renderPage("teacher");
    await screen.findByTestId("rev-de-kho.docx");
    await u.click(screen.getByRole("switch", { name: "Của tôi" }));
    await waitFor(() => expect(lastBody(fetch, "/review/documents/search").mine).toBe(true));
    expect(searchOf().get("mine")).toBe("true");
  });

  it("org admins assign a reviewer", async () => {
    const fetch = mockFetch(
      route("POST", "/api/review/documents/search", searchPage([reviewRow()])),
      route("POST", "/api/users/search", searchPage([gv])),
      route("PATCH", "/api/review/documents/d1", reviewRow({ assigned_to: "u1" })),
    );
    const u = userEvent.setup();
    renderPage("org_admin");
    await screen.findByTestId("rev-de-kho.docx");
    await u.click(screen.getByRole("combobox", { name: "Người duyệt" }));
    await u.click(await screen.findByRole("option", { name: "Cô Lan" }));
    expect(lastBody(fetch, "/users/search")).toMatchObject({ limit: 1000, filters: { role: { value: ["teacher", "org_admin"] } } });
    await waitFor(() => {
      const call = fetch.mock.calls.find(([url, init]) => url === "/api/review/documents/d1" && (init as RequestInit)?.method === "PATCH");
      expect(JSON.parse(String((call?.[1] as RequestInit).body))).toEqual({ assigned_to: "u1" });
    });
  });
});
