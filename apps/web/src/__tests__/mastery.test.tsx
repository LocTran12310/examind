import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ClassOverview } from "@/components/page-components/ClassDetail/ClassOverview/ClassOverview";
import { level, MasteryList } from "@/components/page-components/MyStats/MasteryList/MasteryList";

describe("mastery UI", () => {
  it("lists tracked topics weakest first with the bands the server decided", () => {
    render(
      <MasteryList
        rows={[
          { topic_id: "1", parent_id: null, name: "Vectơ", path: "a", depth: 1, mastery: 0.9, answers: 8, tracked: true, enough_data: true, weak: false },
          { topic_id: "2", parent_id: null, name: "Mệnh đề", path: "b", depth: 1, mastery: 0.2, answers: 6, tracked: true, enough_data: true, weak: true },
          { topic_id: "3", parent_id: null, name: "Hàm số", path: "d", depth: 1, mastery: 0.3, answers: 3, tracked: true, enough_data: false, weak: false },
          { topic_id: "4", parent_id: null, name: "Đại số", path: "c", depth: 1, mastery: 0.5, answers: 8, tracked: false, enough_data: true, weak: true },
        ]}
      />,
    );
    const text = screen.getByTestId("mastery").textContent ?? "";
    expect(text.indexOf("Mệnh đề")).toBeLessThan(text.indexOf("Vectơ"));
    expect(text).not.toContain("Đại số");
    expect(text).toContain("Chưa đủ dữ liệu");
    // the bands read the server's flags, so "Cần ôn" is the one weak rule and never a threshold of our own
    expect(level({ mastery: 0.85, enough_data: true, weak: false })).toBe("Vững");
    expect(level({ mastery: 0.55, enough_data: true, weak: true })).toBe("Cần ôn");
    expect(level({ mastery: 0.55, enough_data: true, weak: false })).toBe("Khá");
    expect(level({ mastery: 0.3, enough_data: false, weak: false })).toBe("Chưa đủ dữ liệu");
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
