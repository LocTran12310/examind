"use client";

import ReactMarkdown, { defaultUrlTransform } from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

/** `asset:<uuid>` → the authenticated asset endpoint; everything else goes through the safe default. */
export function resolveUrl(url: string): string {
  const m = /^asset:([0-9a-f-]{36})$/i.exec(url);
  return m ? `/api/assets/${m[1]}` : defaultUrlTransform(url);
}

export function Markdown({ children, className }: { children: string; className?: string }) {
  if (!children?.trim()) return null;
  return (
    <div className={`prose-question ${className ?? ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkMath, remarkGfm]}
        rehypePlugins={[rehypeKatex]}
        urlTransform={resolveUrl}
        components={{
          // eslint-disable-next-line @next/next/no-img-element
          img: ({ src, alt }) => <img src={typeof src === "string" ? src : undefined} alt={alt || "Hình minh họa"} className="my-2 max-h-80 max-w-full rounded border border-gray-100" loading="lazy" />,
          table: ({ children }) => <table className="my-2 border-collapse text-sm [&_td]:border [&_td]:px-2 [&_th]:border [&_th]:px-2">{children}</table>,
          p: ({ children }) => <p className="my-1.5 leading-relaxed">{children}</p>,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
