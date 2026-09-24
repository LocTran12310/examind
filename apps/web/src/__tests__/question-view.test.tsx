import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { QuestionView } from "@/components/common/QuestionView/QuestionView";
import type { Question } from "@/interfaces/question.interface";

const q = (o: Partial<Question> = {}): Question => ({
  id: "q1", type: "mcq", stem: "Đề bài", options: [], answer: null, solution: "", difficulty: null,
  grade: null, status: "approved", ...o,
} as Question);

describe("QuestionView", () => {
  it("shows an option that is a bare number (AC-01)", () => {
    // the four options of a real question in the bank; every one of them rendered blank before
    const opts = ["108.", "31.", "13.", "36."].map((content, i) => ({ label: "ABCD"[i], content }));
    render(<QuestionView question={q({ options: opts })} mode="review" number={1} />);
    for (const { content } of opts) expect(screen.getByText(content)).toBeInTheDocument();
  });

  it("keeps a real numbered list in the stem a list (AC-03)", () => {
    const { container } = render(<QuestionView question={q({ stem: "Xét các mệnh đề:\n\n1. một\n2. hai" })} mode="review" number={1} />);
    expect(container.querySelectorAll("ol li")).toHaveLength(2);
  });
});
