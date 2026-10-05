import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { describe, expect, it } from "vitest";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { asPhrase, splitMath, textInMath } from "@/lib/common/markdown";

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

describe("splitMath", () => {
  it("cuts a Vietnamese sentence out of a formula, spaces and all (math-rendering AC-1.2)", () => {
    expect(splitMath("-Ở góc phần tư thứ tư thì : \\sin \\alpha <0; \\cos \\alpha >0")).toEqual([
      { tex: "-" }, { text: "Ở góc phần tư thứ tư thì " }, { tex: ": \\sin \\alpha <0; \\cos \\alpha >0" }]);
    expect(splitMath("\\Rightarrow chỉ có đáp án thỏa mãn")).toEqual([{ tex: "\\Rightarrow" }, { text: " chỉ có đáp án thỏa mãn" }]);
  });

  it("keeps a single letter a variable and plain words between Vietnamese ones as words", () => {
    expect(splitMath("Vì a là số dương")).toEqual([{ text: "Vì " }, { tex: "a" }, { text: " là số dương" }]);
    expect(splitMath("x>0 thì khi nào y<0")).toEqual([{ tex: "x>0" }, { text: " thì khi nào " }, { tex: "y<0" }]);
    expect(splitMath("Khi đó x=1")).toEqual([{ text: "Khi đó " }, { tex: "x=1" }]);   // unmarked words at the edges too
    expect(splitMath("x \sin x")).toEqual([{ tex: "x \sin x" }]);
  });

  it("sets words that cannot leave the formula as \\text{}", () => {
    expect(splitMath("\\frac{số học sinh}{n}")).toEqual([{ tex: "\\frac{\\text{số học sinh}}{n}" }]);
    expect(splitMath("\\left( với x>0 \\right)")).toEqual([{ tex: "\\left(\\text{ với }x>0 \\right)" }]);
    expect(splitMath("S_{đáy}")).toEqual([{ tex: "S_{\\text{đáy}}" }]);
    expect(textInMath("x>0 thì y<0")).toBe("x>0\\text{ thì }y<0");
  });

  it("leaves symbols, variables and existing text in one piece, untouched (math-rendering AC-1.3)", () => {
    for (const s of ["T=5\\cos x+4\\sin x", "\\frac{1}{\\sin^2 x}", "α+π=2×3÷6", "\\text{Ở góc} x", "\\mathrm{Ở góc}",
      "\\operatorname{sin}x", "\\left( -\\frac{1}{\\sqrt{10}} \\right)", "\\\\ ab", "\\text{a{b}c}+1", "\\{x\\}"]) {
      expect(splitMath(s)).toEqual([{ tex: s }]);
      expect(textInMath(s)).toBe(s);
    }
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

  it("reads Vietnamese inside $…$ as prose between two formulas (math-rendering AC-1.2)", () => {
    const { container } = render(<Markdown>{"$-Ở góc phần tư thứ tư thì : \\sin \\alpha <0$."}</Markdown>);
    const p = container.querySelector("p")!;
    expect(p.querySelectorAll(":scope > .katex")).toHaveLength(2);
    expect([...p.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent))
      .toEqual(["Ở góc phần tư thứ tư thì ", "."]);
    expect(container.querySelector(".katex-error")).toBeNull();
  });

  it("keeps a display block whole and sets its words as \\text{}", () => {
    const { container } = render(<Markdown>{"$$\nx>0 \\Rightarrow đúng\n$$"}</Markdown>);
    expect(container.querySelectorAll(".katex-display")).toHaveLength(1);
    expect(container.querySelector(".katex-html .text")?.textContent).toContain("đ");
  });
});
