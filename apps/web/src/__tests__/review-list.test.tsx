import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MeProvider } from "@/hooks/common/use-me";
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
  review_state: "pending",
  pending: 6,
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
  it("one state per document, with how many questions still wait", async () => {
    const fetch = mockFetch(route("POST", "/api/review/documents/search", searchPage([reviewRow()])));
    renderPage("teacher");
    const r = await screen.findByTestId("rev-de-kho.docx");
    const row = r.closest("tr")!;
    expect(row).toHaveTextContent("Cần xem");
    expect(row).toHaveTextContent("còn 6 câu");
    expect(row).toHaveTextContent("25%");
    // the six badges are not in the row any more, they are one click away
    expect(row).not.toHaveTextContent("Tự duyệt 3");
    expect(screen.getByRole("link", { name: "Duyệt 6 câu" })).toHaveAttribute("href", "/org/review/d1");
    // and the list opens on the papers that still need work
    await waitFor(() => expect(lastBody(fetch, "/review/documents/search").filters).toEqual({ review_state: { value: "pending" } }));
  });

  it("the state filter goes to the server and the URL", async () => {
    const fetch = mockFetch(route("POST", "/api/review/documents/search", searchPage([reviewRow()])));
    const u = userEvent.setup();
    renderPage("teacher");
    await screen.findByTestId("rev-de-kho.docx");
    await u.click(screen.getByRole("combobox", { name: "Lọc Trạng thái" }));
    await u.click(await screen.findByRole("option", { name: "Xong" }));
    await waitFor(() => expect(lastBody(fetch, "/review/documents/search").filters).toEqual({ review_state: { value: "done" } }));
    expect(searchOf().get("review_state")).toBe("done");
  });

  it("the counts stay one click away and the sample explains itself", async () => {
    mockFetch(route("POST", "/api/review/documents/search", searchPage([reviewRow()])));
    const u = userEvent.setup();
    renderPage("teacher");
    await screen.findByTestId("rev-de-kho.docx");
    // the sentence that says what the sample is (A-02) is on the screen itself
    expect(screen.getAllByText(/5% số câu hệ thống tự duyệt/).length).toBeGreaterThan(0);
    await u.click(screen.getByRole("button", { name: "Chi tiết" }));
    const popover = await screen.findByRole("dialog");
    expect(popover).toHaveTextContent("Tự duyệt 3");
    expect(popover).toHaveTextContent("Cần xem 5");
    expect(popover).toHaveTextContent("Mẫu kiểm chứng 1");
    expect(popover).toHaveTextContent("Đã duyệt 0");
    expect(popover).not.toHaveTextContent("Kiểm tra ngẫu nhiên");
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
