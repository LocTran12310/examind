import { useEffect, useMemo, useState } from "react";
import type { BankFacets } from "@/interfaces/question.interface";
import type { Tag } from "@/interfaces/tag.interface";
import { periodOptions, periodValue } from "@/lib/exam-period";
import { type BankQuery, type Changes, clearAll, list, SHEET_KEYS } from "@/lib/page-libs/bank/filters";

/** The draft of the "Bộ lọc" sheet: edited freely, applied to the URL at once (A-04, A-05). */
export function useFilterSheet({ open, value, tags, facets, onApply, onOpenChange }: {
  open: boolean;
  value: BankQuery;
  tags: Tag[];
  facets?: BankFacets | null;
  onApply: (changes: Changes) => void;
  onOpenChange: (o: boolean) => void;
}) {
  const [draft, setDraft] = useState<BankQuery>(value);
  useEffect(() => {
    if (open) setDraft(value);
  }, [open, value]);
  const set = (changes: Changes) =>
    setDraft((d) => {
      const n = { ...d };
      for (const [k, v] of Object.entries(changes)) {
        if (v === null || v === "") delete n[k];
        else n[k] = v;
      }
      return n;
    });

  const topicIds = list(draft.topic_ids ?? draft.topic_id);
  const tagIds = list(draft.tag_ids);
  const count = (rec: Record<string, number> | undefined, k: string) => rec?.[k] ?? 0;
  const years = useMemo(() => Object.keys(facets?.school_years ?? {}).sort().reverse(), [facets]);

  return {
    draft,
    set,
    topicIds,
    tagIds,
    toggleTag: (id: string) => set({ tag_ids: (tagIds.includes(id) ? tagIds.filter((x) => x !== id) : [...tagIds, id]).join(",") || null }),
    sources: tags.filter((t) => t.group === "source"),
    others: tags.filter((t) => t.group !== "source"),
    count,
    years,
    periods: periodOptions().filter((o) => count(facets?.periods, o.value) > 0 || o.value === periodValue(draft.semester_code, draft.exam_kind)),
    changed: SHEET_KEYS.filter((k) => (draft[k] ?? "") !== (value[k] ?? "")),
    clearDraft: () => setDraft((d) => Object.fromEntries(Object.entries(d).filter(([k]) => !(SHEET_KEYS as readonly string[]).includes(k)))),
    apply: () => {
      const changes: Changes = { ...clearAll };
      for (const k of SHEET_KEYS) if (draft[k]) changes[k] = draft[k];
      onApply(changes);
      onOpenChange(false);
    },
  };
}
