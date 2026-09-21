import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BlueprintEditor } from "@/components/exams/BlueprintEditor";
import { ExamQuestions, moved } from "@/components/exams/ExamQuestions";
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
    await userEvent.click(within(screen.getByRole("listbox")).getByText("Đại số"));
    fireEvent.change(screen.getByLabelText("Số câu"), { target: { value: "6" } });
    await userEvent.click(screen.getByRole("button", { name: "Tạo đề theo ma trận" }));
    expect(onGenerate).toHaveBeenCalledWith([{ type: "mcq", count: 6, topic_id: "ds" }]);
  });

  it("question list: sections, move, swap, remove, points", async () => {
    const onMove = vi.fn(), onSwap = vi.fn(), onRemove = vi.fn(), onPoints = vi.fn();
    render(<ExamQuestions questions={[eq(1), eq(2), eq(3, "II")]} onMove={onMove} onSwap={onSwap} onRemove={onRemove} onPoints={onPoints} />);
    expect(screen.getByText("Phần I")).toBeInTheDocument();
    expect(screen.getByText("Phần II")).toBeInTheDocument();
    await userEvent.click(within(screen.getByTestId("eq-2")).getByRole("button", { name: "Lên" }));
    expect(onMove).toHaveBeenCalledWith("q2", -1);
    await userEvent.click(within(screen.getByTestId("eq-1")).getByRole("button", { name: "Đổi câu" }));
    expect(onSwap).toHaveBeenCalledWith("q1");
    const pts = screen.getByLabelText("Điểm câu 3");
    fireEvent.change(pts, { target: { value: "1" } });
    fireEvent.blur(pts);
    expect(onPoints).toHaveBeenCalledWith("q3", 1);
    expect(moved(["a", "b", "c"], "b", 1)).toEqual(["a", "c", "b"]);
    expect(moved(["a", "b"], "a", -1)).toEqual(["a", "b"]);
  });
});
