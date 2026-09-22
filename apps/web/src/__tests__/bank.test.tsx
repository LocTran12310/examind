import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import BankPage from "@/app/(app)/org/bank/page";
import { BankFilters } from "@/components/bank/BankFilters";
import { QuestionRow } from "@/components/bank/QuestionRow";
import type { BankFacets, ParsedQuestion, Tag, Taxonomy, Topic } from "@/lib/types";
import { lastQuery, mockFetch, route } from "./helpers";
import { searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const taxonomy: Taxonomy = { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [{ id: "g", level: 10, name: "Lớp 10", school_level_name: "Trung học phổ thông" }], semesters: [] };
const topics: Topic[] = [
  { id: "ds", subject_id: "s", parent_id: null, name: "Đại số", level_kind: "strand", grade: null, path: "a", depth: 1, sort: 0, child_count: 1 },
  { id: "hs", subject_id: "s", parent_id: "ds", name: "Hàm số bậc hai và đồ thị", level_kind: "topic", grade: 10, path: "a.b", depth: 2, sort: 0, child_count: 0 },
];

describe("bank", () => {
  it("the sheet applies filters of the subject with counts, chips remove them one by one", async () => {
    const onChange = vi.fn();
    const u = userEvent.setup();
    const tags: Tag[] = [
      { id: "nb", group: "source", name: "Sở GD&ĐT Ninh Bình", subject_id: null },
      { id: "dbien", group: "method", name: "Đổi biến", subject_id: "s" },
    ];
    const facets: BankFacets = { subjects: { s: 5 }, topics: { ds: 4, hs: 3 }, types: { mcq: 3, true_false: 2 }, difficulties: {}, grades: { "10": 5 },
      periods: { "|Thi thử": 4, "hk2|Giữa kỳ": 1 }, school_years: { "2024-2025": 5 }, tags: { nb: 4 } };
    const { rerender } = render(<BankFilters value={{}} onChange={onChange} taxonomy={taxonomy} topics={topics} tags={tags} facets={facets} subjectName="Toán" />);
    await u.type(screen.getByPlaceholderText(/Tìm nội dung/), "parabol");
    await waitFor(() => expect(onChange).toHaveBeenLastCalledWith({ q: "parabol" }), { timeout: 1500 });
    await u.click(screen.getByRole("button", { name: "Bộ lọc" }));
    const sheet = await screen.findByTestId("filter-sheet");
    expect(within(sheet).getByText("Bộ lọc · Toán")).toBeInTheDocument();
    const tree = within(sheet).getByRole("tree", { name: "Cây chuyên đề" });
    expect(tree).toHaveTextContent("Đại số4");
    await u.click(within(tree).getByRole("checkbox", { name: "Đại số" }));
    expect(within(tree).getByRole("checkbox", { name: "Hàm số bậc hai và đồ thị" })).toBeChecked(); // parent includes children
    await u.click(within(within(sheet).getByRole("group", { name: "Đợt kiểm tra" })).getByRole("button", { name: /Thi thử/ }));
    await u.click(within(sheet).getByRole("checkbox", { name: "Sở GD&ĐT Ninh Bình" }));
    await u.click(within(sheet).getByRole("button", { name: "Áp dụng (3)" }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ topic_ids: "ds", exam_kind: "Thi thử", tag_ids: "nb", semester_code: null, type: null }));
    rerender(<BankFilters value={{ topic_ids: "ds", exam_kind: "Thi thử", tag_ids: "nb" }} onChange={onChange} taxonomy={taxonomy} topics={topics} tags={tags} facets={facets} />);
    const chips = screen.getByRole("list", { name: "Bộ lọc đang dùng" });
    expect(within(chips).getAllByRole("listitem").map((c) => c.textContent)).toEqual(["Đại số", "Thi thử", "Sở GD&ĐT Ninh Bình"]);
    expect(screen.getByRole("button", { name: "Bộ lọc (3)" })).toBeInTheDocument();
    await u.click(screen.getByRole("button", { name: "Bỏ lọc Thi thử" }));
    expect(onChange).toHaveBeenLastCalledWith({ semester_code: null, exam_kind: null });
    await u.click(screen.getByRole("button", { name: "Xóa tất cả" }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ topic_ids: null, tag_ids: null, exam_kind: null }));
  });

  it("the page keeps filters in the URL and pages on the server", async () => {
    setUrl("/org/bank?subject_id=s&grade=10&page=2");
    const q = (id: string) => ({ id, type: "mcq", stem: `Câu ${id}`, difficulty: null, grade: 10, status: "approved", tags: [], topics: [] });
    const fetch = mockFetch(
      route("GET", /^\/api\/questions\?/, { items: [q("x1"), q("x2")], total: 45, page: 2, page_size: 20 }),
      route("GET", /^\/api\/questions\/facets\?/, { subjects: { s: 45 }, topics: {}, types: {}, difficulties: {}, grades: {}, periods: {}, school_years: {}, tags: {} }),
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", "/api/topics?subject_id=s", topics),
      route("GET", /^\/api\/tags\?/, { items: [], total: 0, page: 1, page_size: 1000 }),
    );
    const u = userEvent.setup();
    render(<BankPage />);
    await screen.findByText("Câu x1");
    const first = lastQuery(fetch, "/questions");
    expect([first.get("subject_id"), first.get("grade"), first.get("page")]).toEqual(["s", "10", "2"]);
    expect(screen.getByText("Hiển thị 21–40 trên 45 kết quả")).toBeInTheDocument();
    expect(lastQuery(fetch, "/tags").get("subject_id")).toBe("s");
    await u.click(screen.getByRole("button", { name: "Trang sau" }));
    await waitFor(() => expect(lastQuery(fetch, "/questions").get("page")).toBe("3"));
    expect(searchOf().get("grade")).toBe("10");
  });

  it("opens on the subject with most questions; switching subject drops topic and tag filters only", async () => {
    setUrl("/org/bank?type=mcq&topic_ids=ds&tag_ids=nb");
    const two: Taxonomy = { ...taxonomy, subjects: [...taxonomy.subjects, { id: "ly", code: "ly", name: "Vật lý" }] };
    mockFetch(
      route("GET", /^\/api\/questions\?/, { items: [], total: 0, page: 1, page_size: 20 }),
      route("GET", /^\/api\/questions\/facets\?/, { subjects: { s: 5, ly: 9, none: 2 }, topics: {}, types: {}, difficulties: {}, grades: {}, periods: {}, school_years: {}, tags: {} }),
      route("GET", "/api/taxonomy", two),
      route("GET", /^\/api\/topics\?/, []),
      route("GET", /^\/api\/tags\?/, { items: [], total: 0, page: 1, page_size: 1000 }),
    );
    const u = userEvent.setup();
    render(<BankPage />);
    await waitFor(() => expect(searchOf().get("subject_id")).toBe("ly"));
    const tabs = screen.getByRole("tablist", { name: "Môn học" });
    expect(within(tabs).getAllByRole("tab").map((t) => t.textContent)).toEqual(["Toán5", "Vật lý9", "Chưa phân môn 2"]);
    await u.click(within(tabs).getByRole("tab", { name: /Toán/ }));
    await waitFor(() => expect(searchOf().get("subject_id")).toBe("s"));
    expect([searchOf().get("topic_ids"), searchOf().get("tag_ids"), searchOf().get("type")]).toEqual([null, null, "mcq"]);
  });

  it("rows show type, difficulty, status and topic", () => {
    const q = { id: "q1", type: "mcq", stem: "Tọa độ đỉnh parabol", difficulty: "th", grade: 10, status: "approved", tags: [{ id: "t", group: "source", name: "Đề A" }],
      topics: [{ id: "hs", name: "Hàm số bậc hai và đồ thị", is_primary: true, source: "manual", score: 1 }] } as unknown as ParsedQuestion;
    render(<ul><QuestionRow q={q} selected={false} onToggle={() => {}} /></ul>);
    const row = screen.getByTestId("bank-q1");
    for (const text of ["Trắc nghiệm", "Thông hiểu", "Lớp 10", "Đã duyệt", "Hàm số bậc hai và đồ thị", "#Đề A"]) expect(row).toHaveTextContent(text);
    expect(within(row).getByRole("link")).toHaveAttribute("href", "/org/bank/q1");
  });
});
