"use client";

import { Network, Search, X } from "lucide-react";
import { useState } from "react";
import { FormDialog } from "@/components/app/FormDialog";
import { OptionSelect } from "@/components/app/OptionSelect";
import { DebouncedInput } from "@/components/data-table/FilterCell";
import { Button } from "@/components/ui/button";
import { DIFFICULTY_LABEL, EXAM_KINDS, STATUS_LABEL, TYPE_LABEL, type Tag, type Taxonomy, type Topic } from "@/lib/types";
import { TopicPicker, topicLabel } from "./TopicPicker";

export type BankQuery = Record<string, string>;
type Changes = Record<string, string | null>;

const opts = (rec: Record<string, string>) => Object.entries(rec).map(([value, label]) => ({ value, label }));

/** Filters for the question bank; every change goes to the URL (and so to the server). */
export function BankFilters({ value, onChange, taxonomy, topics, tags }: { value: BankQuery; onChange: (c: Changes) => void; taxonomy: Taxonomy; topics: Topic[]; tags: Tag[] }) {
  const [picking, setPicking] = useState(false);
  const set = (k: string, v: string) => onChange({ [k]: v || null });
  const byId = new Map(topics.map((t) => [t.id, t]));
  const topic = value.topic_id ? byId.get(value.topic_id) : undefined;
  const sel = "h-8 w-auto min-w-32";
  return (
    <div className="grid gap-3 border-b p-3" data-testid="bank-filters">
      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
        <DebouncedInput aria-label="Tìm nội dung" className="pl-8" placeholder="Tìm nội dung câu hỏi (không cần dấu)…" value={value.q ?? ""} onChange={(v) => set("q", v)} />
      </div>
      <div className="flex flex-wrap gap-2">
        <OptionSelect className={sel} aria-label="Môn" value={value.subject_id ?? ""} onValueChange={(v) => set("subject_id", v)} emptyLabel="Mọi môn" options={taxonomy.subjects.map((s) => ({ value: s.id, label: s.name }))} />
        <OptionSelect className={sel} aria-label="Lớp" value={value.grade ?? ""} onValueChange={(v) => set("grade", v)} emptyLabel="Mọi lớp" options={taxonomy.grades.map((g) => ({ value: String(g.level), label: g.name, group: g.school_level_name ?? undefined }))} />
        <OptionSelect className={sel} aria-label="Học kỳ" value={value.semester_code ?? ""} onValueChange={(v) => set("semester_code", v)} emptyLabel="Mọi học kỳ" options={taxonomy.semesters.map((s) => ({ value: s.code, label: s.name }))} />
        <OptionSelect className={sel} aria-label="Loại đề" value={value.exam_kind ?? ""} onValueChange={(v) => set("exam_kind", v)} emptyLabel="Mọi loại đề" options={EXAM_KINDS.map((k) => ({ value: k, label: k }))} />
        <OptionSelect className={sel} aria-label="Loại câu" value={value.type ?? ""} onValueChange={(v) => set("type", v)} emptyLabel="Mọi loại câu" options={opts(TYPE_LABEL)} />
        <OptionSelect className={sel} aria-label="Mức độ" value={value.difficulty ?? ""} onValueChange={(v) => set("difficulty", v)} emptyLabel="Mọi mức độ" options={opts(DIFFICULTY_LABEL)} />
        <OptionSelect
          className={sel}
          aria-label="Trạng thái"
          value={value.status ?? "usable"}
          onValueChange={(v) => set("status", v === "usable" ? "" : v)}
          options={[{ value: "usable", label: "Dùng được" }, { value: "all", label: "Tất cả" }, ...opts(STATUS_LABEL as Record<string, string>)]}
        />
        <OptionSelect className={sel} aria-label="Tag" value={value.tag_ids ?? ""} onValueChange={(v) => set("tag_ids", v)} emptyLabel="Mọi tag" options={tags.map((t) => ({ value: t.id, label: t.name }))} />
        <Button variant="outline" size="sm" className="h-8" onClick={() => setPicking(true)} data-testid="topic-filter">
          <Network /> {topic ? `Chuyên đề: ${topic.name}` : "Chuyên đề…"}
        </Button>
        {topic && (
          <Button variant="ghost" size="icon-sm" onClick={() => set("topic_id", "")} aria-label="Bỏ lọc chuyên đề">
            <X />
          </Button>
        )}
      </div>
      {topic && <p className="text-xs text-muted-foreground">Gồm cả các nhánh con của {topicLabel(topic, byId)}</p>}
      <FormDialog open={picking} title="Lọc theo chuyên đề" onOpenChange={setPicking}>
        <TopicPicker
          topics={topics}
          onPick={(t) => {
            setPicking(false);
            set("topic_id", t.id);
          }}
          onClose={() => setPicking(false)}
        />
      </FormDialog>
    </div>
  );
}
