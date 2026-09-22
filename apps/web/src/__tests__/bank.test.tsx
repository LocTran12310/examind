import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import BankPage from "@/app/(app)/org/bank/page";
import { BankFilters } from "@/components/bank/BankFilters";
import { QuestionRow } from "@/components/bank/QuestionRow";
import type { ParsedQuestion, Taxonomy, Topic } from "@/lib/types";
import { lastQuery, mockFetch, route } from "./helpers";
import { searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const taxonomy: Taxonomy = { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [{ id: "g", level: 10, name: "Lớp 10" }], semesters: [] };
const topics: Topic[] = [
  { id: "ds", subject_id: "s", parent_id: null, name: "Đại số", level_kind: "strand", grade: null, path: "a", depth: 1, sort: 0, child_count: 1 },
  { id: "hs", subject_id: "s", parent_id: "ds", name: "Hàm số bậc hai và đồ thị", level_kind: "topic", grade: 10, path: "a.b", depth: 2, sort: 0, child_count: 0 },
];

describe("bank", () => {
  it("filters update the query and topic filter explains the subtree", async () => {
    const onChange = vi.fn();
    const u = userEvent.setup();
    const { rerender } = render(<BankFilters value={{}} onChange={onChange} taxonomy={taxonomy} topics={topics} tags={[]} />);
    await u.type(screen.getByPlaceholderText(/Tìm nội dung/), "parabol");
    await waitFor(() => expect(onChange).toHaveBeenLastCalledWith({ q: "parabol" }), { timeout: 1500 });
    await u.click(screen.getByRole("combobox", { name: "Lớp" }));
    await u.click(await screen.findByRole("option", { name: "Lớp 10" }));
    expect(onChange).toHaveBeenLastCalledWith({ grade: "10" });
    await u.click(screen.getByTestId("topic-filter"));
    await u.type(screen.getByPlaceholderText(/Tìm chuyên đề/), "dai so");
    await u.click(within(screen.getByRole("listbox")).getByText("Đại số"));
    expect(onChange).toHaveBeenLastCalledWith({ topic_id: "ds" });
    rerender(<BankFilters value={{ topic_id: "ds" }} onChange={onChange} taxonomy={taxonomy} topics={topics} tags={[]} />);
    expect(screen.getByText(/Gồm cả các nhánh con của Đại số/)).toBeInTheDocument();
  });

  it("the page keeps filters in the URL and pages on the server", async () => {
    setUrl("/org/bank?grade=10&page=2");
    const q = (id: string) => ({ id, type: "mcq", stem: `Câu ${id}`, difficulty: null, grade: 10, status: "approved", tags: [], topics: [] });
    const fetch = mockFetch(
      route("GET", /^\/api\/questions\?/, { items: [q("x1"), q("x2")], total: 45, page: 2, page_size: 20 }),
      route("GET", "/api/taxonomy", taxonomy),
      route("GET", "/api/topics", topics),
      route("GET", /^\/api\/tags\?/, { items: [], total: 0, page: 1, page_size: 1000 }),
    );
    const u = userEvent.setup();
    render(<BankPage />);
    await screen.findByText("Câu x1");
    const first = lastQuery(fetch, "/questions");
    expect([first.get("grade"), first.get("page")]).toEqual(["10", "2"]);
    expect(screen.getByText("Hiển thị 21–40 trên 45 kết quả")).toBeInTheDocument();
    await u.click(screen.getByRole("button", { name: "Trang sau" }));
    await waitFor(() => expect(lastQuery(fetch, "/questions").get("page")).toBe("3"));
    expect(searchOf().get("grade")).toBe("10");
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
