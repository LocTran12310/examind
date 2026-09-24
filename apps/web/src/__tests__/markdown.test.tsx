import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { asPhrase } from "@/lib/common/markdown";

describe("asPhrase", () => {
  it("escapes what would open a block, and nothing else", () => {
    // the whole reason this exists: "9." is the number nine, not a list starting at nine
    expect(asPhrase("9.")).toBe("9\\.");
    expect(asPhrase("108.")).toBe("108\\.");
    expect(asPhrase("9)")).toBe("9\\)");
    expect(asPhrase("- 5")).toBe("\\- 5");
    expect(asPhrase("# 5")).toBe("\\# 5");
    expect(asPhrase("> 5")).toBe("\\> 5");
    // content that never opened a block is handed over untouched
    for (const s of ["$-5$.", "9", "A. 9.", "x = 9.", "Đúng", "![](asset:abc)"]) expect(asPhrase(s)).toBe(s);
  });

  it("works line by line, because an option can wrap", () => {
    expect(asPhrase("một\n9.")).toBe("một\n9\\.");
  });
});

describe("Markdown", () => {
  it("renders a numeric option instead of swallowing it (AC-01)", () => {
    render(<Markdown phrase>9.</Markdown>);
    expect(screen.getByText("9.")).toBeInTheDocument();
  });

  it("leaves formulas, words and images alone (AC-02)", () => {
    const { container } = render(<Markdown phrase>{"$-5$."}</Markdown>);
    expect(container.querySelector(".katex")).not.toBeNull();
    expect(container.textContent).toContain(".");
    render(<Markdown phrase>Đúng</Markdown>);
    expect(screen.getByText("Đúng")).toBeInTheDocument();
  });

  it("keeps a real numbered list a list where the content is a document (AC-03)", () => {
    const { container } = render(<Markdown>{"1. một\n2. hai"}</Markdown>);
    expect(container.querySelectorAll("ol li")).toHaveLength(2);
  });

  it("without the phrase mode, a bare number is still swallowed — which is why options ask for it", () => {
    const { container } = render(<Markdown>9.</Markdown>);
    expect(container.querySelector("ol")).not.toBeNull();     // an ordered list…
    expect(container.textContent?.trim()).toBe("");           // …with nothing in it
  });
});
