"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { NO_SUBJECT } from "@/constants/question.constant";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";

type Subject = Taxonomy["subjects"][number];

/** Môn as tabs, with how many rows each one holds.
 *
 *  The bank works inside one subject (subject-scoped-bank ADR-01), so it offers no "all" tab: there is no
 *  honest topic tree across subjects. A list that is not scoped that way — the exams — passes `allLabel` and
 *  gets a first tab whose value is the empty scope. Subjects holding nothing are hidden unless chosen;
 *  "Chưa phân môn" appears only when such rows exist. */
export function SubjectTabs({ subjects, counts, value, onChange, allLabel }: { subjects: Subject[]; counts?: Record<string, number>; value: string; onChange: (id: string) => void; allLabel?: string }) {
  const shown = subjects.filter((s) => !counts || counts[s.id] || s.id === value);
  const none = counts?.[NO_SUBJECT] ?? 0;
  return (
    <Tabs value={value} onValueChange={onChange} className="min-w-0">
      <TabsList aria-label="Môn học" className="max-w-full justify-start overflow-x-auto">
        {allLabel && (
          <TabsTrigger value="" className="flex-none">
            {allLabel}
            {counts && <span className="text-xs tabular-nums text-muted-foreground">{Object.values(counts).reduce((a, b) => a + b, 0).toLocaleString("vi-VN")}</span>}
          </TabsTrigger>
        )}
        {(shown.length ? shown : subjects).map((s) => (
          <TabsTrigger key={s.id} value={s.id} className="flex-none">
            {s.name}
            {counts && <span className="text-xs tabular-nums text-muted-foreground">{(counts[s.id] ?? 0).toLocaleString("vi-VN")}</span>}
          </TabsTrigger>
        ))}
        {(none > 0 || value === NO_SUBJECT) && (
          <TabsTrigger value={NO_SUBJECT} className="flex-none">
            Chưa phân môn <span className="text-xs tabular-nums text-muted-foreground">{none}</span>
          </TabsTrigger>
        )}
      </TabsList>
    </Tabs>
  );
}
