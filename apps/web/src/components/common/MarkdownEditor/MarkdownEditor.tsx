"use client";

import { Bold, Eye, EyeOff, ImagePlus, Italic, Radical, Sigma, SquareFunction } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Markdown } from "@/components/common/Markdown/Markdown";

/** Text inserted around the selection: `before` + selection (or `placeholder`) + `after`. */
type Snippet = { label: string; before: string; after?: string; placeholder?: string; icon?: React.ReactNode; text?: string };

const SNIPPETS: Snippet[] = [
  { label: "In đậm", before: "**", after: "**", placeholder: "chữ đậm", icon: <Bold /> },
  { label: "In nghiêng", before: "*", after: "*", placeholder: "chữ nghiêng", icon: <Italic /> },
  { label: "Công thức trong dòng $…$", before: "$", after: "$", placeholder: "x^2", icon: <Sigma /> },
  { label: "Công thức riêng dòng $$…$$", before: "\n$$\n", after: "\n$$\n", placeholder: "\\int_0^1 f(x)\\,dx", icon: <SquareFunction /> },
  { label: "Phân số", before: "\\frac{", after: "}{}", placeholder: "a", text: "a/b" },
  { label: "Căn bậc hai", before: "\\sqrt{", after: "}", placeholder: "x", icon: <Radical /> },
  { label: "Lũy thừa", before: "^{", after: "}", placeholder: "2", text: "x²" },
  { label: "Chỉ số dưới", before: "_{", after: "}", placeholder: "n", text: "xₙ" },
  { label: "Vectơ", before: "\\overrightarrow{", after: "}", placeholder: "AB", text: "AB⃗" },
  { label: "Góc", before: "\\widehat{", after: "}", placeholder: "ABC", text: "∠" },
  { label: "Nhỏ hơn hoặc bằng", before: "\\le ", text: "≤" },
  { label: "Lớn hơn hoặc bằng", before: "\\ge ", text: "≥" },
  { label: "Khác", before: "\\ne ", text: "≠" },
  { label: "Thuộc", before: "\\in ", text: "∈" },
  { label: "Vô cực", before: "\\infty ", text: "∞" },
  { label: "Tương đương", before: "\\Leftrightarrow ", text: "⇔" },
  { label: "Hệ phương trình", before: "\\begin{cases}", after: "\\end{cases}", placeholder: "x+y=1 \\\\ x-y=0", text: "{" },
];

/** Markdown + LaTeX editor with a toolbar and a live preview (KaTeX errors show in red), so a teacher
 *  sees at once whether a formula is right. Paste or drop images to upload them. */
export function MarkdownEditor({
  value,
  onChange,
  rows = 3,
  compact,
  onFiles,
  uploading,
  "aria-label": ariaLabel,
  id,
  "data-testid": testId,
}: {
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  /** one-line fields (options): toolbar and preview only while focused / when there is markup */
  compact?: boolean;
  onFiles?: (files: File[], at: number) => void;
  uploading?: boolean;
  "aria-label"?: string;
  id?: string;
  "data-testid"?: string;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const file = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState(true);
  const [focused, setFocused] = useState(false);

  function insert(s: Snippet) {
    const el = ref.current;
    const start = el?.selectionStart ?? value.length;
    const end = el?.selectionEnd ?? value.length;
    const picked = value.slice(start, end) || s.placeholder || "";
    const next = value.slice(0, start) + s.before + picked + (s.after ?? "") + value.slice(end);
    onChange(next);
    requestAnimationFrame(() => {
      if (!el) return;
      el.focus();
      const from = start + s.before.length;
      el.setSelectionRange(from, from + picked.length); // the placeholder is selected, ready to type over
    });
  }

  const hasMarkup = /[$*_\\![]/.test(value);
  const showTools = !compact || focused;
  const showPreview = preview && value.trim() !== "" && (!compact || hasMarkup);
  return (
    <div className="grid gap-1" onFocus={() => setFocused(true)} onBlur={(e) => !e.currentTarget.contains(e.relatedTarget as Node) && setFocused(false)}>
      {showTools && (
        <TooltipProvider>
          <div className="flex flex-wrap items-center gap-0.5 rounded-md border bg-muted/40 p-0.5" role="toolbar" aria-label={`Định dạng ${ariaLabel ?? ""}`.trim()}>
            {SNIPPETS.map((s) => (
              <Tooltip key={s.label}>
                <TooltipTrigger asChild>
                  <Button type="button" variant="ghost" size="icon-xs" className={cn(!s.icon && "w-auto px-1.5 text-xs")} aria-label={s.label} onMouseDown={(e) => e.preventDefault()} onClick={() => insert(s)}>
                    {s.icon ?? s.text}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{s.label}</TooltipContent>
              </Tooltip>
            ))}
            {onFiles && (
              <>
                <Button type="button" variant="ghost" size="icon-xs" aria-label="Chèn ảnh" onClick={() => file.current?.click()}>
                  <ImagePlus />
                </Button>
                <Input
                  ref={file}
                  type="file"
                  accept="image/*"
                  hidden
                  multiple
                  onChange={(e) => {
                    if (e.target.files?.length) onFiles([...e.target.files], ref.current?.selectionStart ?? value.length);
                    e.target.value = "";
                  }}
                />
              </>
            )}
            <Button type="button" variant="ghost" size="xs" className="ml-auto" aria-pressed={preview} onClick={() => setPreview((p) => !p)}>
              {preview ? <EyeOff /> : <Eye />} {preview ? "Ẩn xem trước" : "Xem trước"}
            </Button>
          </div>
        </TooltipProvider>
      )}
      <Textarea
        ref={ref}
        id={id}
        aria-label={ariaLabel}
        data-testid={testId}
        rows={rows}
        value={value}
        className={cn("font-mono text-[13px]", compact && "min-h-9")}
        onChange={(e) => onChange(e.target.value)}
        onPaste={(e) => {
          if (onFiles && e.clipboardData.files.length) {
            e.preventDefault();
            onFiles([...e.clipboardData.files], e.currentTarget.selectionStart);
          }
        }}
        onDrop={(e) => {
          if (onFiles && e.dataTransfer.files.length) {
            e.preventDefault();
            onFiles([...e.dataTransfer.files], e.currentTarget.selectionStart);
          }
        }}
      />
      {uploading && <p className="text-xs text-muted-foreground">Đang tải ảnh…</p>}
      {showPreview && (
        <div className="rounded-md border border-dashed bg-muted/20 px-3 py-1.5 text-sm" data-testid={testId ? `${testId}-preview` : undefined} aria-label="Xem trước">
          <Markdown>{value}</Markdown>
        </div>
      )}
    </div>
  );
}
