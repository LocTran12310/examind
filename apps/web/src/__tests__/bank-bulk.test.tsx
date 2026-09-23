import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BulkActions } from "@/components/page-components/Bank/BulkBar/BulkBar";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { mockFetch, renderWithQuery as render, route } from "./helpers";

const topics: Topic[] = [
  { id: "t1", subject_id: "s", parent_id: null, name: "Vectơ", level_kind: "topic", grade: 10, path: "a", depth: 1, sort: 0, child_count: 0 },
  { id: "t2", subject_id: "s", parent_id: null, name: "Đường tròn", level_kind: "topic", grade: 10, path: "b", depth: 1, sort: 1, child_count: 0 },
];
const taxonomy: Taxonomy = {
  subjects: [{ id: "s", code: "toan", name: "Toán" }, { id: "s2", code: "ly", name: "Vật lý" }],
  grades: [{ id: "g10", level: 10, name: "Lớp 10" }, { id: "g11", level: 11, name: "Lớp 11" }],
  semesters: [],
};
const facets = { subjects: {}, topics: { t1: 4, t2: 0 }, types: {}, difficulties: {}, grades: {}, periods: {}, school_years: {}, tags: {} };
const onPage = [{ id: "a", number: 7, stem: "Cho hàm số bậc hai" }, { id: "b", number: 7, stem: "Đường tròn tâm I" }] as ParsedQuestion[];
/** the refusal the API answers when a bulk subject would leave a question in another subject's tree (A-04) */
const conflictBody = {
  code: "subject_topic_conflict",
  message: "2 câu đang có chuyên đề thuộc môn khác (Vectơ, Đường tròn). Bỏ hoặc đổi chuyên đề của những câu đó trước khi đổi môn.",
  details: {
    requestId: "r1",
    fields: {
      subject_id: "2 câu đang có chuyên đề thuộc môn khác.",
      conflicts: [
        { question_id: "a", topic_id: "t1", topic_name: "Vectơ" },
        { question_id: "b", topic_id: "t2", topic_name: "Đường tròn" },
      ],
    },
  },
};

afterEach(() => vi.unstubAllGlobals());

describe("bulk actions", () => {
  it("disabled without selection", () => {
    render(<BulkActions ids={[]} topics={topics} tags={[]} onDone={() => {}} onClear={() => {}} />);
    expect(screen.getByRole("button", { name: /Mức độ/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Xóa" })).toBeDisabled();
  });

  it("sets difficulty and topic for the selection", async () => {
    const f = mockFetch(route("POST", "/api/questions/bulk", { updated: 2 }));
    const onDone = vi.fn();
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b"]} topics={topics} tags={[]} onDone={onDone} onClear={() => {}} />);
    await u.click(screen.getByRole("button", { name: /Mức độ/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Vận dụng" }));
    await u.click(screen.getByRole("button", { name: "Chuyên đề" }));
    await u.click(within(await screen.findByRole("tree", { name: "Cây chuyên đề" })).getByText("Vectơ"));
    await waitFor(() => expect(f).toHaveBeenCalledTimes(2));
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ ids: ["a", "b"], set: { difficulty: "vd" } });
    expect(JSON.parse(String(f.mock.calls[1][1]?.body))).toEqual({ ids: ["a", "b"], set: { primary_topic_id: "t1" } });
    expect(onDone).toHaveBeenCalledTimes(2);
  });

  it("deletes each selected question after confirmation", async () => {
    const f = mockFetch(route("DELETE", "/api/questions/a", undefined, 204), route("DELETE", "/api/questions/b", { code: "question_in_use", message: "x" }, 409));
    const onClear = vi.fn();
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b"]} topics={topics} tags={[]} onDone={() => {}} onClear={onClear} />);
    await u.click(screen.getByRole("button", { name: "Xóa" }));
    expect(f).not.toHaveBeenCalled();
    await u.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xóa" }));
    await waitFor(() => expect(onClear).toHaveBeenCalled());
    expect(f).toHaveBeenCalledTimes(2);
  });

  it("sets a subject and a grade for the selection through the same bulk command (AC-05)", async () => {
    const f = mockFetch(route("POST", "/api/questions/bulk", { updated: 2 }));
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b"]} topics={topics} tags={[]} taxonomy={taxonomy} onDone={() => {}} onClear={() => {}} />);
    await u.click(screen.getByRole("button", { name: /Môn/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Vật lý" }));
    await waitFor(() => expect(f).toHaveBeenCalledTimes(1));
    await u.click(screen.getByRole("button", { name: /Lớp/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Lớp 11" }));
    await waitFor(() => expect(f).toHaveBeenCalledTimes(2));
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ ids: ["a", "b"], set: { subject_id: "s2" } });
    // the grade goes as the number the organisation teaches, like a single edit sends it
    expect(JSON.parse(String(f.mock.calls[1][1]?.body))).toEqual({ ids: ["a", "b"], set: { grade: 11 } });
  });

  it("a subject the topics contradict is refused whole and the conflict is shown, not swallowed (A-04)", async () => {
    mockFetch((url, init) => (String(url) === "/api/questions/bulk" && init?.method === "POST" ? { status: 422, body: conflictBody } : undefined));
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b"]} topics={topics} tags={[]} taxonomy={taxonomy} questions={onPage} onDone={() => {}} onClear={() => {}} />);
    await u.click(screen.getByRole("button", { name: /Môn/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Vật lý" }));

    const panel = await screen.findByTestId("subject-conflict");
    expect(panel).toHaveTextContent("2 câu đang có chuyên đề thuộc môn khác");
    // which questions, which topic, and what to do about it
    // two papers can both hold a "Câu 7": the stem beside the link says which one is meant
    expect(within(panel).getAllByRole("link", { name: "Câu 7" }).map((a) => a.getAttribute("href"))).toEqual(["/org/bank/a", "/org/bank/b"]);
    expect(panel).toHaveTextContent("Cho hàm số bậc hai");
    expect(panel).toHaveTextContent("Đường tròn tâm I");
    expect(panel).toHaveTextContent("chuyên đề Vectơ");
    expect(panel).toHaveTextContent("chuyên đề Đường tròn");
    expect(panel).toHaveTextContent("Không câu nào bị đổi");
  });

  it("the topic picker counts questions of the subject in hand, asked for when it opens (AC-02, ADR-01)", async () => {
    const f = mockFetch(route("POST", "/api/questions/facets", facets), route("POST", "/api/questions/bulk", { updated: 2 }));
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b"]} topics={topics} subjectId="s" tags={[]} taxonomy={taxonomy} onDone={() => {}} onClear={() => {}} />);
    expect(f).not.toHaveBeenCalled(); // nothing is asked for until a picker needs it
    await u.click(screen.getByRole("button", { name: "Chuyên đề" }));
    const tree = await screen.findByRole("tree", { name: "Cây chuyên đề" });
    await waitFor(() => expect(within(tree).getAllByRole("treeitem").map((x) => x.textContent)).toEqual(["Vectơ4", "Đường tròn0"]));
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toMatchObject({ subject_id: "s" });
  });
});
