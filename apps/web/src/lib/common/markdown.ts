/** A block construct opening a line: an ordered-list marker (`9.`, `9)`), a bullet (`-`, `*`, `+`), a heading
 *  (`#`) or a quote (`>`), with the indent captured so it survives untouched. */
const BLOCK_OPENER = /^([ \t]*)([0-9]{1,9}[.)]|[-*+]|#{1,6}|>)(?=[ \t]|$)/;

/**
 * Escape what would otherwise open a block, for content that is a **phrase rather than a document**
 * (blank-options ADR-01).
 *
 * A multiple-choice option whose text is `9.` is the number nine, but Markdown reads it as an ordered list
 * starting at nine — the digits become the marker, the dot becomes the separator, and nothing is left to show.
 * 104 options of this organisation's 1160 rendered blank that way, and a student sitting one of those papers
 * saw four empty choices. Escaping the opener changes how the parser reads the line and not one character of
 * what the reader sees.
 *
 * Line by line, because an option can wrap; the escape is a backslash, which Markdown renders as nothing.
 */
export function asPhrase(text: string): string {
  return text.split("\n").map((line) => line.replace(BLOCK_OPENER, (_m, indent: string, opener: string) =>
    `${indent}${opener.slice(0, -1)}\\${opener.slice(-1)}`)).join("\n");
}
