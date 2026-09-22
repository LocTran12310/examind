import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import { MarkdownEditor } from "./MarkdownEditor";

function Host({ initial = "" }: { initial?: string }) {
  const [v, setV] = useState(initial);
  return <MarkdownEditor aria-label="Đề bài" data-testid="stem" value={v} onChange={setV} />;
}

describe("MarkdownEditor", () => {
  it("previews formulas live and inserts snippets around the selection", async () => {
    const u = userEvent.setup();
    render(<Host initial="Cho $x^2$ và **y**" />);
    const preview = screen.getByTestId("stem-preview");
    expect(preview.querySelector(".katex")).not.toBeNull();
    expect(preview.querySelector("strong")).toHaveTextContent("y");
    const area = screen.getByTestId("stem") as HTMLTextAreaElement;
    fireEvent.change(area, { target: { value: "AB" } });
    area.setSelectionRange(0, 2);
    await u.click(screen.getByRole("button", { name: "Vectơ" }));
    expect(area.value).toBe("\\overrightarrow{AB}");
    await new Promise((r) => requestAnimationFrame(r)); // the editor re-selects the inserted text
    area.setSelectionRange(0, area.value.length);
    await u.click(screen.getByRole("button", { name: "Công thức trong dòng $…$" }));
    expect(area.value).toBe("$\\overrightarrow{AB}$");
    expect(screen.getByTestId("stem-preview").querySelector(".katex")).not.toBeNull();
  });

  it("a broken formula shows as a KaTeX error in the preview", () => {
    render(<Host initial="Sai $\\frac{1}{$ đây" />);
    expect(screen.getByTestId("stem-preview").querySelector(".katex-error, [style*='color']")).not.toBeNull();
  });
});
