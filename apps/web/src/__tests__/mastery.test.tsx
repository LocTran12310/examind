import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ClassOverview } from "@/components/page-components/ClassDetail/ClassOverview/ClassOverview";
import { level, MasteryList } from "@/components/page-components/MyStats/MasteryList/MasteryList";
import type { ClassOverviewRow, ClassReviewRef } from "@/interfaces/mastery.interface";

const review = (o: Partial<ClassReviewRef> = {}): ClassReviewRef => ({
  assignment_id: "a", title: "Ôn", status: "not_started", open_at: "2026-09-21T02:00:00Z", close_at: "2026-10-25T02:00:00Z", total: 1, ...o,
});
const row = (o: Partial<ClassOverviewRow> = {}): ClassOverviewRow => ({
  student_id: "s", full_name: "An", username: "an", weakest: [{ name: "Mệnh đề", mastery: 0.3, answers: 3 }], review: review(), ...o,
});

describe("mastery UI", () => {
  it("lists tracked topics weakest first with the bands the server decided", () => {
    render(
      <MasteryList
        rows={[
          { topic_id: "1", parent_id: null, name: "Vectơ", path: "a", depth: 1, subject_id: "s1", mastery: 0.9, answers: 8, tracked: true, enough_data: true, weak: false },
          { topic_id: "2", parent_id: null, name: "Mệnh đề", path: "b", depth: 1, subject_id: "s1", mastery: 0.2, answers: 6, tracked: true, enough_data: true, weak: true },
          { topic_id: "3", parent_id: null, name: "Hàm số", path: "d", depth: 1, subject_id: "s1", mastery: 0.3, answers: 3, tracked: true, enough_data: false, weak: false },
          { topic_id: "4", parent_id: null, name: "Đại số", path: "c", depth: 1, subject_id: "s1", mastery: 0.5, answers: 8, tracked: false, enough_data: true, weak: true },
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
    render(<ClassOverview rows={[row({ review: review({ status: "submitted" }) })]} />);
    expect(screen.getByTestId("ov-an")).toHaveTextContent("Mệnh đề 30%");
    expect(screen.getByTestId("ov-an")).toHaveTextContent("Đã làm");
    // the column says what the numbers are and how they are ordered, not that a child's topic is the worst (AC-04, ADR-02)
    expect(screen.getByRole("columnheader", { name: "Mức nắm vững theo chuyên đề (thấp trước)" })).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent("yếu nhất");
  });

  it("the review cell says which paper, given when, due when — not just Đã làm (AC-04)", () => {
    // it used to be one badge reading "Chưa làm", which answered none of the four questions a teacher asks
    render(<ClassOverview rows={[row({ review: review({ title: "Đề ôn cá nhân – An", status: "not_started" }) })]} />);
    const cell = screen.getByTestId("ov-an");
    expect(within(cell).getByRole("link", { name: "Đề ôn cá nhân – An" })).toHaveAttribute("href", "/org/assignments/a");
    expect(cell).toHaveTextContent("giao 21/09/2026 · hạn 25/10/2026");
    expect(cell).toHaveTextContent("Chưa làm");
  });

  it("a deadline gone by with nothing submitted reads as quá hạn; a submitted one does not (AC-05)", () => {
    const past = { open_at: "2026-09-01T00:00:00Z", close_at: "2026-09-02T00:00:00Z" };
    render(
      <ClassOverview
        rows={[row({ review: review({ ...past, status: "not_started" }) }), row({ username: "binh", student_id: "s2", review: review({ ...past, status: "submitted" }) })]}
      />,
    );
    expect(screen.getByTestId("ov-an")).toHaveTextContent("Quá hạn");
    // once the work is in, the deadline has nothing left to warn about
    expect(screen.getByTestId("ov-binh")).toHaveTextContent("Đã làm");
    expect(screen.getByTestId("ov-binh")).not.toHaveTextContent("Quá hạn");
  });

  it("three papers do not look like one: the cell says how many came before (AC-06)", () => {
    render(<ClassOverview rows={[row({ review: review({ total: 3 }) })]} />);
    expect(screen.getByTestId("ov-an")).toHaveTextContent("còn 2 đề trước");
  });

  it("never assigned says so instead of leaving the cell blank (AC-07)", () => {
    render(<ClassOverview rows={[row({ review: null })]} />);
    expect(screen.getByTestId("ov-an")).toHaveTextContent("chưa giao");
  });
});
