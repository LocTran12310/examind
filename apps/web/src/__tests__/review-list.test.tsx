import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ReviewList } from "@/components/review/ReviewList";
import type { ReviewDocument, User } from "@/lib/types";

const row: ReviewDocument = {
  document: { id: "d1", filename: "de-kho.docx" } as ReviewDocument["document"],
  total: 8,
  counts: { auto_approved: 3, needs_review: 5, approved: 0, rejected: 0, duplicate: 0, flagged: 0 },
  spot_pending: 1,
  progress: 0.25,
  assigned_to: null,
  assigned_name: null,
};
const gv = { id: "u1", full_name: "Cô Lan" } as User;

describe("review list", () => {
  it("shows counts, spot checks, progress and the pending link", () => {
    render(<ReviewList rows={[row]} teachers={[gv]} canAssign={false} onAssign={() => {}} />);
    const r = screen.getByTestId("rev-de-kho.docx");
    expect(r).toHaveTextContent("Tự duyệt 3");
    expect(r).toHaveTextContent("Cần xem 5");
    expect(r).toHaveTextContent("Kiểm tra ngẫu nhiên 1");
    expect(r).toHaveTextContent("25%");
    expect(screen.getByRole("link", { name: "Duyệt 6 câu" })).toHaveAttribute("href", "/org/review/d1");
  });

  it("org admins assign a reviewer", async () => {
    const onAssign = vi.fn();
    render(<ReviewList rows={[row]} teachers={[gv]} canAssign onAssign={onAssign} />);
    await userEvent.selectOptions(screen.getByLabelText("Người duyệt"), "u1");
    expect(onAssign).toHaveBeenCalledWith("d1", "u1");
  });
});
