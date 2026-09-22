import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Question } from "@/interfaces/question.interface";
import { resolveUrl } from "@/components/common/Markdown/Markdown";
import { QuestionView } from "./QuestionView";

const ID1 = "11111111-1111-1111-1111-111111111111";
const ID2 = "22222222-2222-2222-2222-222222222222";

const q: Question = {
  id: "q",
  type: "mcq",
  stem: "Cho $y = x^2 - 4x + 3$. Chọn đáp án đúng.",
  options: [
    { label: "A", content: "$x = 1$" },
    { label: "B", content: "$x = 2$" },
    { label: "C", content: `Hình dưới\n\n![](asset:${ID1})` },
    { label: "D", content: "$x = 4$" },
  ],
  answer: { key: "C" },
  solution: `Bước 1: $x_I = 2$\n\n![](asset:${ID2})`,
  difficulty: "th",
  grade: 10,
  status: "approved",
};

describe("QuestionView", () => {
  it("resolves asset refs and keeps unsafe urls out", () => {
    expect(resolveUrl(`asset:${ID1}`)).toBe(`/api/assets/${ID1}`);
    expect(resolveUrl("javascript:alert(1)")).toBe("");
  });

  it("review mode renders KaTeX, images in their parts, answer and solution", () => {
    const { container } = render(<QuestionView question={q} mode="review" number={1} />);
    expect(container.querySelectorAll(".katex").length).toBeGreaterThan(2);
    const optC = screen.getByTestId("option-C");
    expect(within(optC).getByRole("img")).toHaveAttribute("src", `/api/assets/${ID1}`);
    expect(optC).toHaveAttribute("data-correct", "true");
    expect(screen.getByTestId("answer")).toHaveTextContent("Đáp án: C");
    const sol = screen.getByTestId("solution");
    expect(within(sol).getByRole("img")).toHaveAttribute("src", `/api/assets/${ID2}`);
  });

  it("exam mode hides answer and solution and lets the student pick", async () => {
    const onSelect = vi.fn();
    render(<QuestionView question={q} mode="exam" onSelect={onSelect} />);
    expect(screen.queryByTestId("answer")).toBeNull();
    expect(screen.queryByTestId("solution")).toBeNull();
    expect(screen.getByTestId("option-C")).not.toHaveAttribute("data-correct");
    await userEvent.click(screen.getByTestId("option-B"));
    expect(onSelect).toHaveBeenCalledWith("B");
  });

  it("empty parts render nothing", () => {
    render(<QuestionView question={{ ...q, options: [], solution: "", answer: null, type: "essay" }} mode="review" />);
    expect(screen.queryByTestId("options")).toBeNull();
    expect(screen.queryByTestId("solution")).toBeNull();
    expect(screen.queryByTestId("answer")).toBeNull();
  });

  it("true/false shows per-statement verdicts", () => {
    const tf: Question = { ...q, type: "true_false", answer: {}, options: [{ label: "a", content: "S1", is_true: true }, { label: "b", content: "S2", is_true: false }] };
    render(<QuestionView question={tf} mode="review" />);
    expect(screen.getByTestId("answer")).toHaveTextContent("a) Đ b) S");
  });
});
