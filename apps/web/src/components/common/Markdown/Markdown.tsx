"use client";

import ReactMarkdown, { defaultUrlTransform } from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { asPhrase, splitMath, textInMath } from "@/lib/common/markdown";

/** `asset:<uuid>` → the authenticated asset endpoint; everything else goes through the safe default. */
export function resolveUrl(url: string): string {
  const m = /^asset:([0-9a-f-]{36})$/i.exec(url);
  return m ? `/api/assets/${m[1]}` : defaultUrlTransform(url);
}

type HastNode = { type: string; value?: string; properties?: { className?: unknown }; children?: HastNode[] };

const classesOf = (node: HastNode) => (Array.isArray(node.properties?.className) ? node.properties.className : []);
const textOf = (node: HastNode): string => node.value ?? node.children?.map(textOf).join("") ?? "";

/** Runs before KaTeX: Vietnamese inside a formula reads as words, not as italic variables (see `splitMath`).
 *  An inline formula is cut into formula · prose · formula; a display block stays whole and gets `\text{}`. */
function rehypeTextInMath() {
  const visit = (node: HastNode) => {
    node.children = node.children?.flatMap((child) => {
      const classes = classesOf(child);
      if (classes.includes("math-inline")) {
        return splitMath(textOf(child)).filter((part) => "text" in part || part.tex.trim())
          .map((part) => ("text" in part ? { type: "text", value: part.text } : { ...child, children: [{ type: "text", value: part.tex }] }));
      }
      if (classes.includes("math-display") || classes.includes("language-math")) {
        child.children = [{ type: "text", value: textInMath(textOf(child)) }];
        return [child];
      }
      visit(child);
      return [child];
    });
  };
  return (tree: HastNode) => visit(tree);
}

/** `phrase` renders content that is a phrase rather than a document — an answer option, not an exercise — so a
 *  line opening with `9.` stays the number nine instead of becoming an empty ordered list (ADR-01). */
export function Markdown({ children, className, phrase }: { children: string; className?: string; phrase?: boolean }) {
  if (!children?.trim()) return null;
  const source = phrase ? asPhrase(children) : children;
  return (
    <div className={`prose-question ${className ?? ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkMath, remarkGfm]}
        rehypePlugins={[rehypeTextInMath, rehypeKatex]}
        urlTransform={resolveUrl}
        components={{
          // eslint-disable-next-line @next/next/no-img-element
          img: ({ src, alt }) => <img src={typeof src === "string" ? src : undefined} alt={alt || "Hình minh họa"} className="my-2 max-h-80 max-w-full rounded border border-border" loading="lazy" />,
          table: ({ children }) => <Table className="my-2 w-auto border-collapse">{children}</Table>,
          thead: ({ children }) => <TableHeader>{children}</TableHeader>,
          tbody: ({ children }) => <TableBody>{children}</TableBody>,
          tr: ({ children }) => <TableRow className="hover:bg-transparent">{children}</TableRow>,
          th: ({ children, style }) => <TableHead style={style} className="h-auto border px-2 py-1 whitespace-normal">{children}</TableHead>,
          td: ({ children, style }) => <TableCell style={style} className="border px-2 py-1 whitespace-normal">{children}</TableCell>,
          p: ({ children }) => <p className="my-1.5 leading-relaxed">{children}</p>,
        }}
      >
        {source}
      </ReactMarkdown>
    </div>
  );
}
