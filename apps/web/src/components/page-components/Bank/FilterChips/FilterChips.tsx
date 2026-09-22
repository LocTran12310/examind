"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { type Changes, type Chip, clearAll } from "@/lib/page-libs/bank/filters";

/** Active filters as chips; × removes one, "Xóa tất cả" removes every sheet filter (AC-04). */
export function FilterChips({ chips, onChange }: { chips: Chip[]; onChange: (c: Changes) => void }) {
  if (!chips.length) return null;
  return (
    <div className="flex flex-wrap items-center gap-1.5" aria-label="Bộ lọc đang dùng" role="list">
      {chips.map((c) => (
        <span key={c.key} role="listitem" className="inline-flex max-w-72 items-center gap-1 rounded-full border bg-secondary py-0.5 pr-0.5 pl-2.5 text-xs text-secondary-foreground">
          <span className="truncate" title={c.label}>
            {c.label}
          </span>
          <Button variant="ghost" size="icon-xs" className="size-5 rounded-full" aria-label={`Bỏ lọc ${c.label}`} onClick={() => onChange(c.remove)}>
            <X />
          </Button>
        </span>
      ))}
      {chips.length > 1 && (
        <Button variant="link" size="xs" onClick={() => onChange(clearAll)}>
          Xóa tất cả
        </Button>
      )}
    </div>
  );
}
