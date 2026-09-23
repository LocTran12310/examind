import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReviewCounts, ReviewStateCell } from "@/components/page-components/Review/ReviewCounts/ReviewCounts";
import { FlagPanel } from "@/components/page-components/ReviewDocument/FlagPanel/FlagPanel";
import type { ReviewDocument } from "@/interfaces/review.interface";

describe("flagged questions", () => {
  it("review list counts suspect keys", () => {
    const row: ReviewDocument = {
      document: { id: "d", filename: "de.docx" } as ReviewDocument["document"], total: 40,
      counts: { auto_approved: 30, needs_review: 0, approved: 8, rejected: 0, duplicate: 0, flagged: 2 }, spot_pending: 0, progress: 0.95,
      review_state: "pending", pending: 2, assigned_to: null, assigned_name: null,
    };
    const { container } = render(<ReviewCounts r={row} />);
    expect(container).toHaveTextContent("Nghi sai đáp án 2");
    // the suspect keys are what still waits, and the state column says so
    const state = render(<ReviewStateCell r={row} />).container;
    expect(state).toHaveTextContent("Cần xem");
    expect(state).toHaveTextContent("còn 2 câu");
  });

  it("evidence panel explains the flag", () => {
    render(<FlagPanel ev={{ reason: "80% học sinh nhóm giỏi chọn B, đáp án đang là A", answers: 12, key: "A", overall_correct: 0.1,
      top_quartile: { size: 3, choice: "B", share: 0.8 }, option_counts: { A: 1, B: 9, C: 2 } }} />);
    const p = screen.getByTestId("flag-panel");
    expect(p).toHaveTextContent("nhóm giỏi chọn B");
    expect(p).toHaveTextContent("A: 8% (đáp án hiện tại)");
    expect(p).toHaveTextContent("B: 75%");
  });
});
