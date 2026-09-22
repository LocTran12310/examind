"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { NO_SUBJECT } from "@/constants/question.constant";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";

type Subject = Taxonomy["subjects"][number];

/** The bank works inside one subject (subject-scoped-bank ADR-01). Subjects without questions are
 *  hidden unless chosen; "Chưa phân môn" appears only when such questions exist. */
export function SubjectTabs({ subjects, counts, value, onChange }: { subjects: Subject[]; counts?: Record<string, number>; value: string; onChange: (id: string) => void }) {
  const shown = subjects.filter((s) => !counts || counts[s.id] || s.id === value);
  const none = counts?.[NO_SUBJECT] ?? 0;
  return (
    <Tabs value={value} onValueChange={onChange} className="min-w-0">
      <TabsList aria-label="Môn học" className="max-w-full justify-start overflow-x-auto">
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
