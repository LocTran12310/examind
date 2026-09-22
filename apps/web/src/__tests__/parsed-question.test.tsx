import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { metaChips, ParsedQuestionCard } from "@/components/page-components/DocumentDetail/ParsedQuestionCard/ParsedQuestionCard";
import type { ParsedQuestion } from "@/lib/types";

const q = (o: Partial<ParsedQuestion> = {}): ParsedQuestion => ({
  id: "q", type: "mcq", stem: "Tọa độ đỉnh parabol", options: [], answer: { key: "A" }, solution: "x", difficulty: null, grade: 10,
  status: "draft", number: 1, part: null, confidence: 1, issues: [], parse_method: "rule", parse_model: null, answer_source: "inline",
  subject_id: "s", semester_code: "hk1", exam_kind: "Giữa kỳ", tags: [{ id: "t", group: "source", name: "THPT A" }],
  topics: [{ id: "tp", name: "Tìm đỉnh và trục đối xứng parabol", is_primary: true, source: "auto", score: 0.8 }], ...o,
});

describe("parsed question chips", () => {
  it("shows metadata, source tag and the suggested topic with score", () => {
    render(<ParsedQuestionCard q={q()} meta={metaChips(q(), "Toán")} />);
    const chips = screen.getByTestId("chips");
    expect(chips).toHaveTextContent("Toán · Lớp 10 · Giữa kỳ 1");
    expect(chips).toHaveTextContent("#THPT A");
    expect(screen.getByTestId("topic-chip")).toHaveTextContent("Chuyên đề: Tìm đỉnh và trục đối xứng parabol · 80% · gợi ý");
  });

  it("marks AI suggestions and missing topics", () => {
    const { rerender } = render(<ParsedQuestionCard q={q({ topics: [{ id: "x", name: "Xác suất", is_primary: true, source: "ai", score: 0.66 }] })} />);
    expect(screen.getByTestId("topic-chip")).toHaveTextContent("66% · AI");
    rerender(<ParsedQuestionCard q={q({ topics: [] })} />);
    expect(screen.getByText("Chưa có chuyên đề")).toBeInTheDocument();
  });
});
