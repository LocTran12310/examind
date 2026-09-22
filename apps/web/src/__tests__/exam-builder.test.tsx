import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BlueprintEditor } from "@/components/exams/BlueprintEditor";
import { ExamQuestions, movedTo, swapped } from "@/components/exams/ExamQuestions";
import type { ExamQuestion, Topic } from "@/lib/types";

const topics: Topic[] = [{ id: "ds", subject_id: "s", parent_id: null, name: "Đại số", level_kind: "strand", grade: null, path: "a", depth: 1, sort: 0, child_count: 0 }];
const eq = (n: number, section = "I"): ExamQuestion => ({ id: `q${n}`, type: "mcq", stem: `Câu ${n}`, options: [], answer: null, solution: "", difficulty: null,
  grade: null, status: "approved", number: n, part: null, confidence: 1, issues: [], parse_method: null, parse_model: null, answer_source: null,
  subject_id: null, semester_code: null, exam_kind: null, topics: [], tags: [], position: n, section, points: 0.25, row: 0 });

describe("exam builder", () => {
  it("blueprint rows need a topic, then generate", async () => {
    const onGenerate = vi.fn();
    render(<BlueprintEditor initial={[]} topics={topics} tags={[]} shortfalls={[{ row: 0, missing: 2 }]} onGenerate={onGenerate} />);
    expect(screen.getByRole("button", { name: "Tạo đề theo ma trận" })).toBeDisabled();
    expect(screen.getByTestId("row-0")).toHaveTextContent("thiếu 2 câu");
    await userEvent.click(screen.getByRole("button", { name: "Chọn chuyên đề…" }));
    await userEvent.click(within(screen.getByRole("tree", { name: "Cây chuyên đề" })).getByText("Đại số"));
    fireEvent.change(screen.getByLabelText("Số câu"), { target: { value: "6" } });
    await userEvent.click(screen.getByRole("button", { name: "Tạo đề theo ma trận" }));
    expect(onGenerate).toHaveBeenCalledWith([{ type: "mcq", count: 6, topic_id: "ds" }]);
  });

  it("question list: sections, swap, remove, points", async () => {
    const onSaveOrder = vi.fn(), onSwap = vi.fn(), onRemove = vi.fn(), onPoints = vi.fn();
    render(<ExamQuestions questions={[eq(1), eq(2), eq(3, "II")]} onSaveOrder={onSaveOrder} onSwap={onSwap} onRemove={onRemove} onPoints={onPoints} />);
    expect(screen.getByText("Phần I")).toBeInTheDocument();
    expect(screen.getByText("Phần II")).toBeInTheDocument();
    await userEvent.click(within(screen.getByTestId("eq-1")).getByRole("button", { name: "Đổi câu" }));
    expect(onSwap).toHaveBeenCalledWith("q1");
    const pts = screen.getByLabelText("Điểm câu 3");
    fireEvent.change(pts, { target: { value: "1" } });
    fireEvent.blur(pts);
    expect(onPoints).toHaveBeenCalledWith("q3", 1);
  });

  it("reorders on a draft and saves once: swap with a chosen position, ↑/↓, only inside a part", async () => {
    const onSaveOrder = vi.fn();
    const u = userEvent.setup();
    render(<ExamQuestions questions={[eq(1), eq(2), eq(3), eq(4, "II")]} onSaveOrder={onSaveOrder} onSwap={vi.fn()} onRemove={vi.fn()} onPoints={vi.fn()} />);
    await u.click(screen.getByRole("button", { name: /Sắp xếp thứ tự/ }));
    expect(screen.getByRole("button", { name: /Lưu thứ tự/ })).toBeDisabled();
    await u.click(screen.getByRole("combobox", { name: "Đổi chỗ câu 1 với" }));
    const opts = await screen.findAllByRole("option");
    expect(opts.map((o) => o.textContent)).toEqual(["Đổi chỗ với…", "Câu 2", "Câu 3"]); // not câu 4 (Phần II)
    await u.click(screen.getByRole("option", { name: "Câu 3" }));
    await u.click(screen.getByRole("button", { name: "Đưa câu 1 xuống" }));
    expect(onSaveOrder).not.toHaveBeenCalled(); // nothing saved while editing
    expect(screen.getByRole("button", { name: "Đưa câu 4 lên" })).toBeDisabled();
    await u.click(screen.getByRole("button", { name: /Lưu thứ tự \(3 vị trí đổi\)/ }));
    expect(onSaveOrder).toHaveBeenCalledTimes(1);
    expect(onSaveOrder).toHaveBeenCalledWith(["q2", "q3", "q1", "q4"]);
    expect(movedTo(["a", "b", "c"], "a", "c")).toEqual(["b", "c", "a"]);
    expect(movedTo(["a", "b", "c"], "c", "a")).toEqual(["c", "a", "b"]);
    expect(swapped(["a", "b", "c"], "a", "c")).toEqual(["c", "b", "a"]);
  });
});
