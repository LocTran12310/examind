"use client";

import { useEffect, useRef } from "react";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Kbd } from "@/components/ui/kbd";
import { SUGGESTION_SOURCE_LABEL } from "@/constants/question.constant";
import type { QueueRow, QueueSuggestion } from "@/lib/page-libs/tagging-queue/rows";
import { cn } from "@/lib/utils";

/** One question waiting for a topic: the stem as the bank renders it, where it came from, and the
 *  suggestions as buttons — the first three answer to 1/2/3 while the row is focused (AC-02). */
export function UntaggedRow({
  row,
  focused,
  selected,
  onToggle,
  onFocus,
  onApply,
  onOther,
}: {
  row: QueueRow;
  focused: boolean;
  selected: boolean;
  onToggle: () => void;
  onFocus: () => void;
  onApply: (s: QueueSuggestion) => void;
  onOther: () => void;
}) {
  const box = useRef<HTMLLIElement>(null);
  useEffect(() => {
    if (focused) box.current?.scrollIntoView?.({ block: "nearest" });
  }, [focused]);

  return (
    <li
      ref={box}
      data-testid={`untagged-${row.q.id}`}
      className={cn("flex gap-3 border-b px-3 py-3 last:border-0", focused ? "bg-primary/5 ring-1 ring-primary/30 ring-inset" : "hover:bg-muted/40")}
      onMouseDown={onFocus}
    >
      <Checkbox aria-label="Chọn câu" checked={selected} onCheckedChange={onToggle} className="mt-1" />
      <div className="min-w-0 flex-1">
        <div className="line-clamp-3 text-sm">
          <Markdown>{row.q.stem}</Markdown>
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
          <ToneBadge>{row.subject}</ToneBadge>
          <span className="truncate">{row.document}</span>
          <span>{row.date}</span>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-1">
          {row.suggestions.map((s, i) => (
            <Button
              key={s.topic_id}
              type="button"
              size="xs"
              variant="secondary"
              className="h-auto whitespace-normal bg-primary/10 py-1 text-left font-normal text-primary hover:bg-primary/20"
              onClick={() => onApply(s)}
            >
              {i < 3 && <Kbd className="border border-input bg-transparent font-mono">{i + 1}</Kbd>}
              {s.label}
              <span className="opacity-70">
                {Math.round(s.score * 100)}% · {SUGGESTION_SOURCE_LABEL[s.source] ?? s.source}
              </span>
            </Button>
          ))}
          {row.suggestions.length === 0 && <span className="text-xs text-muted-foreground">Chưa có gợi ý nào</span>}
          <Button type="button" size="xs" variant="outline" onClick={onOther}>
            Chuyên đề khác…
          </Button>
        </div>
      </div>
    </li>
  );
}
