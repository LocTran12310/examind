import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BankFilters } from "@/components/bank/BankFilters";
import { QuestionRow } from "@/components/bank/QuestionRow";
import type { ParsedQuestion, Taxonomy, Topic } from "@/lib/types";

const taxonomy: Taxonomy = { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [{ id: "g", level: 10, name: "Lớp 10" }], semesters: [] };
const topics: Topic[] = [
  { id: "ds", subject_id: "s", parent_id: null, name: "Đại số", level_kind: "strand", grade: null, path: "a", depth: 1, sort: 0, child_count: 1 },
  { id: "hs", subject_id: "s", parent_id: "ds", name: "Hàm số bậc hai và đồ thị", level_kind: "topic", grade: 10, path: "a.b", depth: 2, sort: 0, child_count: 0 },
];

describe("bank", () => {
  it("filters update the query and topic filter explains the subtree", async () => {
    const onChange = vi.fn();
    const { rerender } = render(<BankFilters value={{}} onChange={onChange} taxonomy={taxonomy} topics={topics} tags={[]} />);
    await userEvent.type(screen.getByPlaceholderText(/Tìm nội dung/), "parabol");
    await userEvent.click(screen.getByRole("button", { name: "Tìm" }));
    expect(onChange).toHaveBeenLastCalledWith({ q: "parabol", page: "1" });
    await userEvent.selectOptions(screen.getByLabelText("Lớp"), "10");
    expect(onChange).toHaveBeenLastCalledWith({ grade: "10", page: "1" });
    await userEvent.click(screen.getByTestId("topic-filter"));
    await userEvent.type(screen.getByPlaceholderText(/Tìm chuyên đề/), "dai so");
    await userEvent.click(within(screen.getByRole("listbox")).getByText("Đại số"));
    expect(onChange).toHaveBeenLastCalledWith({ topic_id: "ds", page: "1" });
    rerender(<BankFilters value={{ topic_id: "ds" }} onChange={onChange} taxonomy={taxonomy} topics={topics} tags={[]} />);
    expect(screen.getByText(/Gồm cả các nhánh con của Đại số/)).toBeInTheDocument();
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
