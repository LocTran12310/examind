import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";

describe("FormDialog", () => {
  it("maximises, restores and resizes from its edges", async () => {
    const u = userEvent.setup();
    render(<FormDialog open onOpenChange={() => {}} title="Thêm tag"><p>nội dung</p></FormDialog>);
    const dialog = screen.getByRole("dialog");
    await u.click(screen.getByRole("button", { name: "Phóng to" }));
    expect(dialog).toHaveAttribute("data-maximized", "true");
    expect(dialog.style.width).toContain("100vw");
    await u.click(screen.getByRole("button", { name: "Thu nhỏ" }));
    expect(dialog).not.toHaveAttribute("data-maximized");
    await u.dblClick(screen.getByRole("heading", { name: "Thêm tag" }));
    expect(dialog).toHaveAttribute("data-maximized", "true");
    await u.dblClick(screen.getByRole("heading", { name: "Thêm tag" }));
    // jsdom has no layout: the dialog starts at 0×0, so a drag of the right edge grows it by twice the move
    const right = dialog.querySelector('[data-resize="phải"]')!;
    fireEvent.pointerDown(right, { clientX: 500, clientY: 300, pointerId: 1 });
    fireEvent.pointerMove(window, { clientX: 700, clientY: 300 });
    fireEvent.pointerUp(window);
    expect(dialog.style.width).toBe("400px");
    expect(dialog.style.height).toBe("180px"); // clamped to the minimum
  });
});
