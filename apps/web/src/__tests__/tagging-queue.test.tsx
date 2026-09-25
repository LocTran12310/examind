import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Toaster } from "sonner";
import { describe, expect, it, vi } from "vitest";
import TaggingQueueRoute from "@/app/(app)/org/review/untagged/page";
import type { BankFacets, ParsedQuestion, TopicSuggestion } from "@/interfaces/question.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { lastBody, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const taxonomy: Taxonomy = { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [], semesters: [] };
const topics: Topic[] = [
  { id: "gt", subject_id: "s", parent_id: null, name: "Giải tích", level_kind: "strand", grade: null, path: "a", depth: 1, sort: 0, child_count: 1 },
  { id: "nh", subject_id: "s", parent_id: "gt", name: "Nguyên hàm", level_kind: "topic", grade: 12, path: "a.b", depth: 2, sort: 0, child_count: 0 },
  { id: "tp", subject_id: "s", parent_id: "gt", name: "Tích phân", level_kind: "topic", grade: 12, path: "a.c", depth: 2, sort: 1, child_count: 0 },
];
const doc = { id: "d1", filename: "De-thi-thu-2025.pdf", mime: "application/pdf", size: 1, status: "parsed", error: null, meta: {}, page_count: 2, question_count: 40, log: [], created_at: "2026-09-20T03:00:00Z", finished_at: null };
const facets: BankFacets = { subjects: { s: 2 }, topics: { none: 2 }, types: {}, difficulties: {}, grades: {}, periods: {}, school_years: {}, tags: {}, untagged_documents: { d1: 2 } };
/** what the bank holds per topic of môn Toán — "Tích phân" has nothing yet (AC-02, ADR-01) */
const topicCounts = { gt: 7, nh: 7, tp: 0 };

const question = (id: string, stem: string): ParsedQuestion => ({
  id, type: "mcq", stem, options: [], answer: null, solution: "", difficulty: null, grade: 12, status: "auto_approved",
  number: 1, part: null, confidence: null, issues: [], parse_method: null, parse_model: null, answer_source: null, difficulty_source: null,
  subject_id: "s", semester_code: null, exam_kind: null, topics: [], tags: [], source_document_id: "d1",
});
const suggestion = (topic_id: string, name: string, score: number, source: TopicSuggestion["source"]): TopicSuggestion => ({ topic_id, name, path: `Giải tích › ${name}`, score, source });

/** The queue's backend, with a search answer that can change between calls. */
function stack(pages: ParsedQuestion[][]) {
  let call = 0;
  return mockFetch(
    (url, init) => {
      if (String(url) !== "/api/questions/search" || (init?.method ?? "GET") !== "POST") return undefined;
      const items = pages[Math.min(call++, pages.length - 1)];
      return { body: searchPage(items, items.length) };
    },
    (url, init) => {
      if (String(url) !== "/api/questions/facets" || (init?.method ?? "GET") !== "POST") return undefined;
      // the pickers ask one subject for its topic counts; the page asks for the queue's own facets
      const asked = JSON.parse(String(init?.body ?? "{}")) as { limit?: number };
      return { body: asked.limit === 1 ? { ...facets, topics: topicCounts } : facets };
    },
    route("POST", "/api/questions/suggest-topics", {
      suggestions: {
        q1: [suggestion("nh", "Nguyên hàm", 0.82, "keyword"), suggestion("tp", "Tích phân", 0.44, "similar")],
        q2: [suggestion("tp", "Tích phân", 0.61, "similar")],
      },
    }),
    route("POST", "/api/questions/bulk", { updated: 2 }),
    route("POST", "/api/questions/bulk/topics", { updated: 1, skipped: [{ question_id: "q2", topic_id: "tp", reason: "subject_mismatch", message: "Chuyên đề không thuộc môn của câu hỏi" }] }),
    route("POST", "/api/documents/search", searchPage([doc])),
    route("GET", "/api/taxonomy", taxonomy),
    route("GET", "/api/topics", topics),
  );
}

const twoQuestions = [question("q1", "Tính $\\int x^2 dx$"), question("q2", "Diện tích hình phẳng")];
// q3 is what the rules and the model could not place: it has no suggestion at all
const threeQuestions = [...twoQuestions, question("q3", "Một câu lạ")];

describe("tagging queue", () => {
  it("lists the untagged questions of the search body and asks for the suggestions of the page", async () => {
    setUrl("/org/review/untagged");
    const fetch = stack([twoQuestions]);
    render(<TaggingQueueRoute />);
    await screen.findByTestId("untagged-q1");

    const body = lastBody(fetch, "/questions/search");
    expect(body.has_topic).toBe(false);
    expect(Object.keys(body)[0]).toBe("has_topic"); // at the top of the body, as the contract writes it
    expect(body.sort).toEqual([{ field: "created_at", desc: true }]);
    expect(screen.getByText("Còn 2 câu chưa gắn chuyên đề")).toBeInTheDocument();
    const row = screen.getByTestId("untagged-q1");
    expect(row).toHaveTextContent("Toán");
    expect(row).toHaveTextContent("De-thi-thu-2025.pdf");
    expect(row).toHaveTextContent("20/09/2026");

    await waitFor(() => expect(lastBody(fetch, "/questions/suggest-topics").question_ids).toEqual(["q1", "q2"]));
    // the suggestion says where it came from and how sure it is
    expect(within(row).getByRole("button", { name: /Nguyên hàm/ })).toHaveTextContent("82% · Từ khóa");
    expect(within(row).getByRole("button", { name: /Tích phân/ })).toHaveTextContent("44% · Tương tự");
  });

  it("clicking a suggestion assigns it as primary topic and the row leaves the queue", async () => {
    setUrl("/org/review/untagged");
    const fetch = stack([twoQuestions, [twoQuestions[1]]]);
    const u = userEvent.setup();
    render(<TaggingQueueRoute />);
    const row = await screen.findByTestId("untagged-q1");
    await u.click(await within(row).findByRole("button", { name: /Nguyên hàm/ }));

    await waitFor(() => expect(lastBody(fetch, "/questions/bulk")).toEqual({ ids: ["q1"], set: { primary_topic_id: "nh" } }));
    // the list and the counter come back from the server
    await waitFor(() => expect(screen.queryByTestId("untagged-q1")).not.toBeInTheDocument());
    expect(screen.getByText("Còn 1 câu chưa gắn chuyên đề")).toBeInTheDocument();
    expect(fetch.mock.calls.filter((c) => String(c[0]) === "/api/questions/facets").length).toBeGreaterThan(1);
  });

  it("the 1 key applies the first suggestion of the focused row", async () => {
    setUrl("/org/review/untagged");
    const fetch = stack([twoQuestions, [twoQuestions[1]]]);
    const u = userEvent.setup();
    render(<TaggingQueueRoute />);
    await screen.findByTestId("untagged-q1");
    await waitFor(() => expect(within(screen.getByTestId("untagged-q1")).getByRole("button", { name: /Nguyên hàm/ })).toBeInTheDocument());
    await u.keyboard("1");
    await waitFor(() => expect(lastBody(fetch, "/questions/bulk")).toEqual({ ids: ["q1"], set: { primary_topic_id: "nh" } }));
  });

  it("↓ moves the focus, so 1 applies the next row's own suggestion", async () => {
    setUrl("/org/review/untagged");
    const fetch = stack([twoQuestions, [twoQuestions[0]]]);
    const u = userEvent.setup();
    render(<TaggingQueueRoute />);
    await screen.findByTestId("untagged-q2");
    await waitFor(() => expect(within(screen.getByTestId("untagged-q2")).getByRole("button", { name: /Tích phân/ })).toBeInTheDocument());
    await u.keyboard("{ArrowDown}");
    await u.keyboard("1");
    await waitFor(() => expect(lastBody(fetch, "/questions/bulk")).toEqual({ ids: ["q2"], set: { primary_topic_id: "tp" } }));
  });

  it("bulk apply sends one request for every selected question", async () => {
    setUrl("/org/review/untagged");
    const fetch = stack([twoQuestions, []]);
    const u = userEvent.setup();
    render(<TaggingQueueRoute />);
    await screen.findByTestId("untagged-q1");
    await u.click(screen.getByRole("checkbox", { name: "Chọn cả trang" }));
    await u.click(screen.getByRole("button", { name: "Gán chuyên đề cho 2 câu" }));
    const tree = await screen.findByRole("tree", { name: "Cây chuyên đề" });
    await u.type(screen.getByLabelText("Tìm chuyên đề"), "tich phan");
    await u.click(within(tree).getByText("Tích phân"));

    await waitFor(() => expect(lastBody(fetch, "/questions/bulk")).toEqual({ ids: ["q1", "q2"], set: { primary_topic_id: "tp" } }));
    expect(fetch.mock.calls.filter((c) => String(c[0]) === "/api/questions/bulk").length).toBe(1);
    await waitFor(() => expect(screen.getByText("Còn 0 câu chưa gắn chuyên đề")).toBeInTheDocument());
  });

  it("the document filter goes to the server as a resource parameter", async () => {
    setUrl("/org/review/untagged?document_id=d1");
    const fetch = stack([twoQuestions]);
    render(<TaggingQueueRoute />);
    await screen.findByTestId("untagged-q1");
    expect(lastBody(fetch, "/questions/search").document_id).toBe("d1");
    // the counts per document must not shrink to the chosen one (AC-05)
    expect(lastBody(fetch, "/questions/facets").document_id).toBeUndefined();
  });

  it("the row's picker opens on that row's own suggestion and counts questions, applying nothing (AC-01, AC-02)", async () => {
    setUrl("/org/review/untagged");
    const fetch = stack([twoQuestions]);
    const u = userEvent.setup();
    render(<TaggingQueueRoute />);
    const row = await screen.findByTestId("untagged-q1");
    await waitFor(() => expect(within(row).getByRole("button", { name: /Nguyên hàm/ })).toBeInTheDocument());
    await u.click(within(row).getByRole("button", { name: "Chuyên đề khác…" }));

    const tree = await screen.findByRole("tree", { name: "Cây chuyên đề" });
    const items = within(tree).getAllByRole("treeitem");
    // the branch of the suggestion is open and the suggested topic is the focused row
    expect(items.map((x) => x.textContent)).toEqual(["Giải tích7", "Nguyên hàm7", "Tích phân0"]);
    expect(items[1]).toHaveAttribute("aria-selected", "true");
    // the numbers are questions from the facets of the row's subject, not the count of child topics
    expect(lastBody(fetch, "/questions/facets")).toMatchObject({ subject_id: "s", limit: 1 });
    // nothing is applied until the teacher picks
    expect(fetch.mock.calls.some((c) => String(c[0]).startsWith("/api/questions/bulk"))).toBe(false);
  });

  it("\"Gán theo gợi ý\" sends every row's own suggestion in one request and names what it did not do (AC-03)", async () => {
    setUrl("/org/review/untagged");
    const fetch = stack([threeQuestions, [threeQuestions[2]]]);
    const u = userEvent.setup();
    render(
      <>
        <TaggingQueueRoute />
        <Toaster />
      </>,
    );
    await screen.findByTestId("untagged-q3");
    await waitFor(() => expect(within(screen.getByTestId("untagged-q1")).getByRole("button", { name: /Nguyên hàm/ })).toBeInTheDocument());
    await u.click(screen.getByRole("checkbox", { name: "Chọn cả trang" }));
    // the bar says up front how many of the three the system can place
    expect(screen.getByRole("button", { name: "Gán theo gợi ý (2)" })).toBeEnabled();
    expect(screen.getByText("1 câu chưa có gợi ý")).toBeInTheDocument();
    await u.click(screen.getByRole("button", { name: "Gán theo gợi ý (2)" }));

    await waitFor(() =>
      expect(lastBody(fetch, "/questions/bulk/topics")).toEqual({
        pairs: [
          { question_id: "q1", topic_id: "nh" },
          { question_id: "q2", topic_id: "tp" },
        ],
      }),
    );
    expect(fetch.mock.calls.filter((c) => String(c[0]) === "/api/questions/bulk/topics").length).toBe(1);
    // the question with no suggestion is untouched and named, and so is what the server skipped
    const said = await screen.findByText(/Đã gán chuyên đề cho 1 câu/);
    expect(said).toHaveTextContent("1 câu chưa có gợi ý");
    expect(said).toHaveTextContent("1 câu bị bỏ qua (Chuyên đề không thuộc môn của câu hỏi)");
    await waitFor(() => expect(screen.getByText("Còn 1 câu chưa gắn chuyên đề")).toBeInTheDocument());
  });

  it("the document filter scrolls and asks for the next page at the end of the list (AC-04)", async () => {
    setUrl("/org/review/untagged");
    const u = userEvent.setup();
    const fetch = mockFetch(
      route("POST", "/api/questions/search", searchPage(twoQuestions, 2)),
      route("POST", "/api/questions/facets", { ...facets, untagged_documents: undefined }),
      route("POST", "/api/questions/suggest-topics", { suggestions: {} }),
      // one paper per page of a bank that holds two
      (url, init) => {
        if (String(url) !== "/api/documents/search" || (init?.method ?? "GET") !== "POST") return undefined;
        const { page } = JSON.parse(String(init?.body ?? "{}")) as { page: number };
        return { body: searchPage([{ ...doc, id: `d${page}`, filename: `De-${page}.pdf` }], 2, page, 1) };
      },
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", "/api/topics", topics),
    );
    render(<TaggingQueueRoute />);
    await screen.findByTestId("untagged-q1");
    await u.click(screen.getByRole("combobox", { name: "Đề gốc" }));
    const list = await screen.findByTestId("option-list");
    expect(within(list).getByText("De-1.pdf")).toBeInTheDocument();

    fireEvent.scroll(list);
    await waitFor(() => expect(lastBody(fetch, "/documents/search").page).toBe(2));
    // what was loaded stays: the list grows instead of being replaced
    await waitFor(() => expect(within(screen.getByTestId("option-list")).getByText("De-2.pdf")).toBeInTheDocument());
    expect(within(screen.getByTestId("option-list")).getByText("De-1.pdf")).toBeInTheDocument();
  });
});
