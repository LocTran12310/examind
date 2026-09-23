import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Toaster } from "sonner";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BulkActions } from "@/components/page-components/Bank/BulkBar/BulkBar";
import { QUESTION_EVENT_KEYS, QUESTION_KEYS } from "@/constants/react-query-key.constant";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { lastBody, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";

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
/** a page of the bank as the query keys hold it, to check what an undo refreshes */
const body = { page: 1, limit: 20, subject_id: "s" };
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
  it("disabled without selection, and no count to read", () => {
    render(<BulkActions ids={[]} topics={topics} tags={[]} onDone={() => {}} onClear={() => {}} />);
    expect(screen.getByRole("button", { name: /Mức độ/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Xóa" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Duyệt" })).toBeDisabled();
  });

  it("every action says how many questions it will change (AC-06)", async () => {
    mockFetch(route("POST", "/api/questions/facets", facets));
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b", "c"]} topics={topics} subjectId="s" tags={[{ id: "g1", group: "method", name: "đổi biến" }]} taxonomy={taxonomy} onDone={() => {}} onClear={() => {}} />);
    // the count rides on the button itself, not only on "Đã chọn" at the other end of the toolbar
    for (const label of ["Mức độ", "Môn", "Lớp", "Chuyên đề", "Thêm tag", "Duyệt", "Loại", "Xóa"]) {
      expect(screen.getByRole("button", { name: `${label} 3 câu` })).toBeEnabled();
    }
    // and the menu that opens repeats what it is about to change
    await u.click(screen.getByRole("button", { name: "Mức độ 3 câu" }));
    expect(await screen.findByText("Đặt mức độ cho 3 câu")).toBeInTheDocument();
    await u.keyboard("{Escape}");
    await u.click(screen.getByRole("button", { name: "Chuyên đề 3 câu" }));
    expect(await screen.findByRole("heading", { name: "Đặt chuyên đề cho 3 câu" })).toBeInTheDocument();
  });

  it("sets difficulty and topic for the selection", async () => {
    const f = mockFetch(route("POST", "/api/questions/bulk", { updated: 2 }));
    const onDone = vi.fn();
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b"]} topics={topics} tags={[]} onDone={onDone} onClear={() => {}} />);
    await u.click(screen.getByRole("button", { name: /Mức độ/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Vận dụng" }));
    await u.click(screen.getByRole("button", { name: "Chuyên đề 2 câu" }));
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
    await u.click(screen.getByRole("button", { name: "Xóa 2 câu" }));
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

  it("the toast carries Hoàn tác: the batch goes back, and the bank, its facets and the history refresh (AC-01)", async () => {
    const f = mockFetch(route("POST", "/api/questions/bulk", { updated: 2, batch_id: "batch-1" }), route("POST", "/api/questions/bulk/undo", { restored: 2, batch_id: "batch-2" }));
    const u = userEvent.setup();
    const { client } = render(
      <>
        <BulkActions ids={["a", "b"]} topics={topics} tags={[]} taxonomy={taxonomy} onDone={() => {}} onClear={() => {}} />
        <Toaster />
      </>,
    );
    // what the bank has on screen while the toast is up: the page, the tab counts and "Thay đổi gần đây"
    const seeded = [QUESTION_KEYS.SEARCH(body), QUESTION_KEYS.FACETS(body), QUESTION_EVENT_KEYS.SEARCH(body)];
    for (const key of seeded) client.setQueryData(key, searchPage([]));

    await u.click(screen.getByRole("button", { name: /Lớp/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Lớp 11" }));
    expect(await screen.findByText("Đã đặt Lớp 11: 2 câu")).toBeInTheDocument();

    await u.click(screen.getByRole("button", { name: "Hoàn tác" }));
    await waitFor(() => expect(lastBody(f, "/questions/bulk/undo")).toEqual({ batch_id: "batch-1" }));
    // how many questions came back, not just "xong"
    expect(await screen.findByText("Đã hoàn tác 2 câu")).toBeInTheDocument();
    for (const key of seeded) expect(client.getQueryState(key)?.isInvalidated).toBe(true);
  });

  it("an undo the API refuses is read out in its own words, not as a crash (AC-01)", async () => {
    mockFetch(
      route("POST", "/api/questions/bulk", { updated: 2, batch_id: "batch-1" }),
      route("POST", "/api/questions/bulk/undo", { code: "batch_already_undone", message: "Lượt sửa này đã được hoàn tác", details: { requestId: "r1" } }, 409),
    );
    const u = userEvent.setup();
    render(
      <>
        <BulkActions ids={["a", "b"]} topics={topics} tags={[]} taxonomy={taxonomy} onDone={() => {}} onClear={() => {}} />
        <Toaster />
      </>,
    );
    await u.click(screen.getByRole("button", { name: /Lớp/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Lớp 11" }));
    await u.click(await screen.findByRole("button", { name: "Hoàn tác" }));
    expect(await screen.findByText("Lượt sửa này đã được hoàn tác")).toBeInTheDocument();
  });

  it("an answer with no batch id offers no way back from the toast", async () => {
    // the batch is what an undo names; an edit that does not say which one it wrote cannot be taken back here,
    // and the toast promises nothing it cannot do — "Thay đổi gần đây" is still the way in
    mockFetch(route("POST", "/api/questions/bulk", { updated: 2 }));
    const u = userEvent.setup();
    render(
      <>
        <BulkActions ids={["a", "b"]} topics={topics} tags={[]} taxonomy={taxonomy} onDone={() => {}} onClear={() => {}} />
        <Toaster />
      </>,
    );
    await u.click(screen.getByRole("button", { name: /Lớp/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Lớp 11" }));
    expect(await screen.findByText("Đã đặt Lớp 11: 2 câu")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Hoàn tác" })).not.toBeInTheDocument();
  });

  it("the topic picker counts questions of the subject in hand, asked for when it opens (AC-02, ADR-01)", async () => {
    const f = mockFetch(route("POST", "/api/questions/facets", facets), route("POST", "/api/questions/bulk", { updated: 2 }));
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b"]} topics={topics} subjectId="s" tags={[]} taxonomy={taxonomy} onDone={() => {}} onClear={() => {}} />);
    expect(f).not.toHaveBeenCalled(); // nothing is asked for until a picker needs it
    await u.click(screen.getByRole("button", { name: "Chuyên đề 2 câu" }));
    const tree = await screen.findByRole("tree", { name: "Cây chuyên đề" });
    await waitFor(() => expect(within(tree).getAllByRole("treeitem").map((x) => x.textContent)).toEqual(["Vectơ4", "Đường tròn0"]));
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toMatchObject({ subject_id: "s" });
  });
});
