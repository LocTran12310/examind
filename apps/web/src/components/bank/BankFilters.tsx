"use client";

import { Search, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import { DebouncedInput } from "@/components/data-table/FilterCell";
import { Button } from "@/components/ui/button";
import type { BankFacets, Tag, Taxonomy, Topic } from "@/lib/types";
import { FilterChips } from "./FilterChips";
import { FilterSheet } from "./FilterSheet";
import { type BankQuery, type Changes, chips } from "./filters";

export type { BankQuery } from "./filters";

/** Search + "Bộ lọc (n)" + chips. Every change goes to the URL, and so to the server. */
export function BankFilters({
  value,
  onChange,
  taxonomy,
  topics,
  tags,
  facets,
  subjectName,
}: {
  value: BankQuery;
  onChange: (c: Changes) => void;
  taxonomy: Taxonomy;
  topics: Topic[];
  tags: Tag[];
  facets?: BankFacets | null;
  subjectName?: string;
}) {
  const [open, setOpen] = useState(false);
  const active = chips(value, { taxonomy, topics, tags });
  return (
    <div className="grid gap-2 border-b p-3" data-testid="bank-filters">
      <div className="flex gap-2">
        <div className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <DebouncedInput aria-label="Tìm nội dung" className="pl-8" placeholder="Tìm nội dung câu hỏi (không cần dấu)…" value={value.q ?? ""} onChange={(v) => onChange({ q: v || null })} />
        </div>
        <Button variant={active.length ? "secondary" : "outline"} onClick={() => setOpen(true)}>
          <SlidersHorizontal /> Bộ lọc{active.length ? ` (${active.length})` : ""}
        </Button>
      </div>
      <FilterChips chips={active} onChange={onChange} />
      <FilterSheet open={open} onOpenChange={setOpen} value={value} onApply={onChange} subjectName={subjectName} taxonomy={taxonomy} topics={topics} tags={tags} facets={facets} />
    </div>
  );
}
