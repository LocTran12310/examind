import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ClassOverview } from "@/components/adaptive/ClassOverview";
import { level, MasteryList } from "@/components/adaptive/MasteryList";

describe("mastery UI", () => {
  it("lists tracked topics weakest first with levels", () => {
    render(
      <MasteryList
        rows={[
          { topic_id: "1", parent_id: null, name: "Vectơ", path: "a", depth: 1, mastery: 0.9, answers: 5, tracked: true },
          { topic_id: "2", parent_id: null, name: "Mệnh đề", path: "b", depth: 1, mastery: 0.2, answers: 3, tracked: true },
          { topic_id: "3", parent_id: null, name: "Đại số", path: "c", depth: 1, mastery: 0.5, answers: 8, tracked: false },
        ]}
      />,
    );
    const text = screen.getByTestId("mastery").textContent ?? "";
    expect(text.indexOf("Mệnh đề")).toBeLessThan(text.indexOf("Vectơ"));
    expect(text).not.toContain("Đại số");
    expect(level(0.85)).toBe("Vững");
    expect(level(0.3)).toBe("Cần ôn");
  });

  it("class overview shows weakest topics and review status", () => {
    render(
      <ClassOverview
        rows={[{ student_id: "s", full_name: "An", username: "an", weakest: [{ name: "Mệnh đề", mastery: 0.3, answers: 3 }], review: { assignment_id: "a", title: "Ôn", status: "submitted" } }]}
      />,
    );
    expect(screen.getByTestId("ov-an")).toHaveTextContent("Mệnh đề 30%");
    expect(screen.getByTestId("ov-an")).toHaveTextContent("Đã làm");
  });
});
