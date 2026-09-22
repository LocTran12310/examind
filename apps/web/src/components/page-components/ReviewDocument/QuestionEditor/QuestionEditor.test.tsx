import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { mockFetch, renderWithQuery as render, route } from "@/__tests__/helpers";
import { AnswerKeyDialog } from "@/components/page-components/ReviewDocument/AnswerKeyDialog/AnswerKeyDialog";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import { QuestionEditor } from "./QuestionEditor";

const q: ParsedQuestion = {
  id: "q1", type: "essay", stem: "Giá trị của $2^1$? Các lựa chọn: 1; 2; 3; 4.", options: [], answer: null, solution: "", difficulty: null,
  grade: 10, status: "needs_review", number: 1, part: null, confidence: 0.4, issues: ["không nhận ra phương án"], parse_method: "rule",
  parse_model: null, answer_source: null, subject_id: null, semester_code: null, exam_kind: null, topics: [], tags: [],
};

afterEach(() => vi.unstubAllGlobals());

describe("question editor", () => {
  it("converts to MCQ, previews live and saves with Ctrl+Enter", async () => {
    const f = mockFetch(route("PATCH", "/api/questions/q1", { ...q, type: "mcq" }));
    const onSaved = vi.fn();
    render(<QuestionEditor question={q} onSaved={onSaved} onCancel={() => {}} />);
    await userEvent.click(screen.getByRole("combobox", { name: "Loại câu" }));
    await userEvent.click(await screen.findByRole("option", { name: "Trắc nghiệm 4 phương án" }));
    expect(screen.getByRole("combobox", { name: "Loại câu" })).toHaveTextContent("Trắc nghiệm 4 phương án");
    for (const [i, v] of ["1", "2", "3", "4"].entries()) fireEvent.change(screen.getByLabelText(`Phương án ${"ABCD"[i]}`), { target: { value: v } });
    await userEvent.click(screen.getAllByRole("radio")[1]);
    fireEvent.change(screen.getByTestId("stem"), { target: { value: "Giá trị của $2^1$ bằng" } });
    expect(screen.getByTestId("preview")).toHaveTextContent("Giá trị của");
    fireEvent.keyDown(screen.getByTestId("stem"), { key: "Enter", ctrlKey: true });
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    const body = JSON.parse(String(f.mock.calls[0][1]?.body));
    expect(body).toMatchObject({ type: "mcq", stem: "Giá trị của $2^1$ bằng", answer: { key: "B" } });
    expect(body.options.map((o: { content: string }) => o.content)).toEqual(["1", "2", "3", "4"]);
  });

  it("pasting an image uploads it and inserts the reference", async () => {
    mockFetch(route("POST", "/api/assets", { id: "a", ref: "asset:11111111-1111-1111-1111-111111111111" }, 201));
    render(<QuestionEditor question={q} onSaved={() => {}} onCancel={() => {}} />);
    const stem = screen.getByTestId("stem");
    const file = new File(["png"], "x.png", { type: "image/png" });
    fireEvent.paste(stem, { clipboardData: { files: [file] } });
    await waitFor(() => expect((stem as HTMLTextAreaElement).value).toContain("![](asset:11111111-1111-1111-1111-111111111111)"));
  });

  it("answer key dialog reports the summary", async () => {
    mockFetch(route("POST", "/api/review/documents/d/answer-key", { applied: 5, approved: 4, unmatched: [9] }));
    render(<AnswerKeyDialog docId="d" onDone={() => {}} />);
    await userEvent.type(screen.getByLabelText("Bảng đáp án"), "1B 2B");
    await userEvent.click(screen.getByRole("button", { name: "Áp dụng" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Đã áp dụng 5 đáp án, duyệt 4 câu. Không khớp: câu 9.");
  });
});
