import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Toaster } from "sonner";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import BankRoute from "@/app/(app)/org/bank/page";
import { RecentChanges } from "@/components/page-components/Bank/RecentChanges/RecentChanges";
import type { QuestionEvent } from "@/interfaces/question.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import { lastBody, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";
import { searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const EVENTS = "/api/question-events/search";
const taxonomy: Taxonomy = { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [{ id: "g", level: 10, name: "Lớp 10" }], semesters: [] };
const facets = { subjects: { s: 2 }, topics: {}, types: {}, difficulties: {}, grades: {}, periods: {}, school_years: {}, tags: {} };

const ev = (o: Partial<QuestionEvent> = {}): QuestionEvent => ({
  batch_id: "b1",
  created_at: "2026-09-24T03:12:00Z", // 10:12 on the business calendar
  user_id: "u1",
  actor_name: "Cô Lan",
  action: "bulk",
  fields: ["status", "grade"],
  questions: 2,
  undoable: true,
  reason: null,
  message: null,
  ...o,
});

/** The sheet on its own, open, with the history it is given. */
const openSheet = () =>
  render(
    <>
      <RecentChanges open onOpenChange={() => {}} />
      <Toaster />
    </>,
  );

const rowOf = (text: string | RegExp) => screen.getAllByRole("row").find((r) => (typeof text === "string" ? r.textContent?.includes(text) : text.test(r.textContent ?? "")))!;

beforeEach(() => setUrl("/org/bank?subject_id=s"));
afterEach(() => vi.unstubAllGlobals());

describe("thay đổi gần đây", () => {
  it("one row per lượt sửa — when, who, what it moved, how many câu — newest first (AC-03)", async () => {
    const f = mockFetch(
      route("POST", EVENTS, searchPage([ev(), ev({ batch_id: "b0", created_at: "2026-09-23T09:00:00Z", actor_name: null, action: "topic", fields: ["topics", "primary_topic"], questions: 7 })], 2)),
    );
    openSheet();
    await screen.findByText("Cô Lan");
    // the server's own order; the list asks for nothing but a page (the API sorts newest first)
    expect(lastBody(f, "/question-events/search")).toEqual({ page: 1, limit: 20 });
    const rows = screen.getAllByRole("row").slice(2); // header, then the filter row
    expect(rows[0]).toHaveTextContent("24/09/2026 10:12");
    expect(rows[0]).toHaveTextContent("Cô Lan");
    // the verb and the fields in the teacher's words, not `bulk` and `subject_id`
    expect(rows[0]).toHaveTextContent("Sửa hàng loạt");
    expect(rows[0]).toHaveTextContent("Duyệt, Lớp");
    expect(rows[0]).toHaveTextContent("2");
    expect(rows[1]).toHaveTextContent("Đặt chuyên đề");
    expect(rows[1]).toHaveTextContent("Chuyên đề, Chuyên đề chính");
    expect(rows[1]).toHaveTextContent("Hệ thống"); // a change nobody signed
  });

  it("hoàn tác from a row restores the batch, and the list then comes back changed from the server (AC-04)", async () => {
    let undone = false;
    const before = [ev()];
    // what the server answers once the undo has run: the original is read-only and the undo is a row of its own
    const after = [
      ev({ batch_id: "b2", created_at: "2026-09-24T03:20:00Z", action: "undo", fields: ["status", "grade"], undoable: false, reason: "is_undo", message: "Đây đã là một lần hoàn tác" }),
      ev({ undoable: false, reason: "already_undone", message: "Lượt sửa này đã được hoàn tác" }),
    ];
    const f = mockFetch(
      (url, init) => (String(url) === EVENTS && init?.method === "POST" ? { body: searchPage(undone ? after : before, undone ? 2 : 1) } : undefined),
      (url, init) => {
        if (String(url) !== "/api/questions/bulk/undo" || init?.method !== "POST") return undefined;
        undone = true;
        return { body: { restored: 2, batch_id: "b2" } };
      },
    );
    const u = userEvent.setup();
    openSheet();
    await u.click(await screen.findByRole("button", { name: "Hoàn tác" }));
    await waitFor(() => expect(lastBody(f, "/questions/bulk/undo")).toEqual({ batch_id: "b1" }));
    expect(await screen.findByText("Đã hoàn tác 2 câu")).toBeInTheDocument();

    // the two rows of AC-04 come from the refetch, not from anything this screen decided
    expect(await screen.findByText("Đây đã là một lần hoàn tác")).toBeInTheDocument();
    expect(rowOf("Lượt sửa này đã được hoàn tác")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Hoàn tác" })).not.toBeInTheDocument();
  });

  it("a row that can no longer be taken back says why in the API's own words (AC-05)", async () => {
    mockFetch(
      route(
        "POST",
        EVENTS,
        searchPage([
          ev({ batch_id: "old", questions: 30, undoable: false, reason: "expired", message: "Quá 7 ngày nên không hoàn tác được" }),
          ev({ batch_id: null, questions: 1, undoable: false, reason: "no_batch", message: "Thay đổi được ghi trước khi có hoàn tác" }),
        ], 2),
      ),
    );
    openSheet();
    // the reason takes the button's place — the row stays readable, nothing is hidden
    expect(await screen.findByText("Quá 7 ngày nên không hoàn tác được")).toBeInTheDocument();
    expect(within(rowOf("Thay đổi được ghi trước khi có hoàn tác")).queryByRole("button", { name: "Hoàn tác" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Hoàn tác" })).not.toBeInTheDocument();
  });

  it("an undo the API refuses leaves the row alone and says what it said", async () => {
    mockFetch(
      route("POST", EVENTS, searchPage([ev()], 1)),
      route("POST", "/api/questions/bulk/undo", { code: "questions_gone", message: "Một số câu của lượt sửa này không còn nữa", details: { requestId: "r1" } }, 422),
    );
    const u = userEvent.setup();
    openSheet();
    await u.click(await screen.findByRole("button", { name: "Hoàn tác" }));
    expect(await screen.findByText("Một số câu của lượt sửa này không còn nữa")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hoàn tác" })).toBeEnabled();
  });

  it("pages on the server, under its own URL prefix so the bank underneath keeps its place", async () => {
    const f = mockFetch((url, init) => {
      if (String(url) !== EVENTS || init?.method !== "POST") return undefined;
      const { page } = JSON.parse(String(init?.body ?? "{}")) as { page: number };
      return { body: searchPage([ev({ batch_id: `b${page}`, questions: page })], 30, page) };
    });
    const u = userEvent.setup();
    openSheet();
    await screen.findByText("Cô Lan");
    await u.click(screen.getByRole("button", { name: "Trang sau" }));
    await waitFor(() => expect(lastBody(f, "/question-events/search")).toMatchObject({ page: 2, limit: 20 }));
    expect(searchOf().get("ch.page")).toBe("2");
    expect(searchOf().get("subject_id")).toBe("s"); // the bank's own filters are untouched
  });

  it("opens from the bank's toolbar, beside the bar whose work it takes back", async () => {
    mockFetch(
      route("POST", "/api/questions/search", searchPage([], 0)),
      route("POST", "/api/questions/facets", facets),
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", /\/api\/topics/, []),
      route("POST", "/api/tags/search", searchPage([])),
      route("POST", EVENTS, searchPage([ev()], 1)),
    );
    const u = userEvent.setup();
    render(<BankRoute />);
    await u.click(await screen.findByRole("button", { name: "Thay đổi gần đây" }));
    const sheet = await screen.findByTestId("recent-changes");
    expect(within(sheet).getByRole("heading", { name: "Thay đổi gần đây" })).toBeInTheDocument();
    expect(await within(sheet).findByText("Sửa hàng loạt")).toBeInTheDocument();
  });
});
