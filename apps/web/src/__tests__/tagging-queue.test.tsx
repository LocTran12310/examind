import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

const question = (id: string, stem: string): ParsedQuestion => ({
  id, type: "mcq", stem, options: [], answer: null, solution: "", difficulty: null, grade: 12, status: "auto_approved",
  number: 1, part: null, confidence: null, issues: [], parse_method: null, parse_model: null, answer_source: null,
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
    route("POST", "/api/questions/facets", facets),
    route("POST", "/api/questions/suggest-topics", {
      suggestions: {
        q1: [suggestion("nh", "Nguyên hàm", 0.82, "keyword"), suggestion("tp", "Tích phân", 0.44, "similar")],
        q2: [suggestion("tp", "Tích phân", 0.61, "similar")],
      },
    }),
    route("POST", "/api/questions/bulk", { updated: 2 }),
    route("POST", "/api/documents/search", searchPage([doc])),
    route("GET", "/api/taxonomy", taxonomy),
    route("GET", "/api/topics", topics),
  );
}

const twoQuestions = [question("q1", "Tính $\\int x^2 dx$"), question("q2", "Diện tích hình phẳng")];

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
});
