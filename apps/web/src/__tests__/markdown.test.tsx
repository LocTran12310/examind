import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
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

describe("Markdown formulas", () => {
  // the stylesheet layout.tsx loads must be the one that matches the HTML the renderer writes: katex 0.18 renamed
  // `.base`/`.strut`/`.sizing`, and 0.16 markup under 0.18 CSS stacked numerators onto the fraction bar
  it("renders with classes the loaded stylesheet styles (math-rendering AC-1.1)", () => {
    const css = readFileSync(createRequire(import.meta.url).resolve("katex/dist/katex.css"), "utf8");
    const { container } = render(<Markdown>{"$T=\\frac{1}{\\sin^2 x}+\\left(-\\frac{3}{\\sqrt{10}}\\right)$"}</Markdown>);
    const used = new Set([...container.querySelectorAll(".katex-html [class]")].flatMap((e) => [...e.classList]));
    const atoms = /^m(ord|rel|open|close|op|bin|inner|punct|tight)$/;   // semantic tags with no rule of their own
    const unstyled = [...used].filter((c) => !atoms.test(c) && !new RegExp(`\\.${c}(?![\\w-])`).test(css));
    expect(used.has("strut")).toBe(true);
    expect(unstyled).toEqual([]);
  });
});
