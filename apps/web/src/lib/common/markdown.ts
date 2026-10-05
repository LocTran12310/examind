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

/** Commands whose argument is already text — their braces are copied through untouched. */
const TEXT_COMMANDS = new Set(["text", "textrm", "textbf", "textit", "textup", "textnormal", "textsf", "texttt", "mbox",
  "hbox", "mathrm", "mathbf", "mathit", "mathsf", "mathtt", "operatorname"]);
/** A letter only a word carries: a tone mark, đ, ơ, ư — Latin-1 and Latin Extended, without × and ÷. */
const MARKED = /[À-ÖØ-öø-ɏḀ-ỿ]/;
const LETTER = /[A-Za-z \tÀ-ÖØ-öø-ɏḀ-ỿ]/;

/** A piece of a formula: still a formula, or Vietnamese that reads as prose. */
export type MathPart = { tex: string } | { text: string };

/** One run of words and spaces: the Vietnamese stretches become text, the rest stays formula. A stretch is words of
 *  two letters or more with at least one marked among them (`Khi đó`, `số học sinh`); a single letter is a variable
 *  and breaks it (`Vì ` · `a` · ` là số`). The spaces on either side travel with the words, or math mode would
 *  swallow them. */
function stretches(run: string): MathPart[] {
  const words = run.split(/([ \t]+)/);   // word, space, word, … — words at even indices, empty at a spaced edge
  const wordy = (k: number) => MARKED.test(words[k]) || words[k].length > 1;
  const parts: MathPart[] = [];
  let tex = "", i = 0;
  while (i < words.length) {
    let end = i - 2;
    for (let k = i; k < words.length && wordy(k); k += 2) end = k;
    const group = end < i ? [] : words.slice(i, end + 1);
    if (!group.some((w) => MARKED.test(w))) { end = Math.max(end, i); tex += words.slice(i, end + 2).join(""); i = end + 2; continue; }
    const lead = words[i - 1] ?? "";
    tex = tex.slice(0, tex.length - lead.length);
    if (tex) parts.push({ tex });
    parts.push({ text: lead + group.join("") + (words[end + 1] ?? "") });
    tex = "";
    i = end + 2;
  }
  if (tex) parts.push({ tex });
  return parts;
}

/**
 * Cut the Vietnamese out of a formula.
 *
 * Imported solutions carry sentences inside `$…$` — `$-Ở góc phần tư thứ tư thì : \sin\alpha<0$` — and in math
 * mode KaTeX drops every space and sets each letter as an italic variable, so the student reads
 * "Ởgócphầntưthứtưthì". A stretch at the top of the formula comes out as prose, in the page's own font; one that
 * cannot leave — inside braces, `\left…\right`, an environment, or right after `^`/`_` — becomes `\text{…}`.
 * Only stretches with a Vietnamese letter move: a formula of symbols, Greek letters and plain variables comes back
 * as one piece, character for character, and so does anything already inside `\text{}`/`\mathrm{}`.
 */
export function splitMath(tex: string): MathPart[] {
  const parts: MathPart[] = [];
  const emit = (part: MathPart) => {
    const last = parts[parts.length - 1];
    if ("tex" in part && last && "tex" in last) last.tex += part.tex;
    else parts.push(part);
  };
  let run = "", depth = 0, i = 0;
  const flush = () => {
    if (!run) return;
    const last = parts[parts.length - 1];
    const nested = depth > 0 || (last && "tex" in last && /[\^_]\s*$/.test(last.tex));
    for (const part of stretches(run)) emit(nested && "text" in part ? { tex: `\\text{${part.text}}` } : part);
    run = "";
  };
  while (i < tex.length) {
    if (LETTER.test(tex[i])) { run += tex[i++]; continue; }
    flush();
    if (tex[i] !== "\\") {
      if (tex[i] === "{") depth++;
      else if (tex[i] === "}") depth--;
      emit({ tex: tex[i++] });
      continue;
    }
    const name = /^\\([A-Za-z]+\*?|.)/.exec(tex.slice(i))?.[0] ?? "\\";
    i += name.length;
    if (name === "\\left" || name === "\\begin") depth++;
    else if (name === "\\right" || name === "\\end") depth--;
    const open = TEXT_COMMANDS.has(name.slice(1).replace("*", "")) ? /^\s*\{/.exec(tex.slice(i)) : null;
    if (!open) { emit({ tex: name }); continue; }
    let level = 0, j = i + open[0].length - 1;
    for (; j < tex.length; j++) {
      if (tex[j] === "\\") { j++; continue; }
      if (tex[j] === "{") level++;
      else if (tex[j] === "}" && --level === 0) break;
    }
    emit({ tex: name + tex.slice(i, j + 1) });
    i = j + 1;
  }
  flush();
  return parts;
}

/** The same cut for a formula that has to stay whole — a display block: every stretch becomes `\text{…}`. */
export function textInMath(tex: string): string {
  return splitMath(tex).map((part) => ("text" in part ? `\\text{${part.text}}` : part.tex)).join("");
}
