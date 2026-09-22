"use client";

import { Network, Search, X } from "lucide-react";
import { useState } from "react";
import { FormDialog } from "@/components/app/FormDialog";
import { OptionSelect } from "@/components/app/OptionSelect";
import { DebouncedInput } from "@/components/data-table/FilterCell";
import { Button } from "@/components/ui/button";
import { parsePeriod, periodOptions, periodValue } from "@/lib/exam-period";
import { DIFFICULTY_LABEL, STATUS_LABEL, TYPE_LABEL, type Tag, type Taxonomy, type Topic } from "@/lib/types";
import { TopicTreeSelect } from "@/components/topics/TopicTreeSelect";
import { topicLabel } from "./TopicPicker";

export type BankQuery = Record<string, string>;
type Changes = Record<string, string | null>;

const opts = (rec: Record<string, string>) => Object.entries(rec).map(([value, label]) => ({ value, label }));

/** Filters for the question bank; every change goes to the URL (and so to the server). */
export function BankFilters({ value, onChange, taxonomy, topics, tags }: { value: BankQuery; onChange: (c: Changes) => void; taxonomy: Taxonomy; topics: Topic[]; tags: Tag[] }) {
  const [picking, setPicking] = useState(false);
  const set = (k: string, v: string) => onChange({ [k]: v || null });
  const byId = new Map(topics.map((t) => [t.id, t]));
  // topic filter: comma list of top-most nodes (each includes its subtree); old links used topic_id
  const chosen = (value.topic_ids ?? value.topic_id ?? "").split(",").filter((id) => byId.has(id));
  const topicText = chosen.length === 1 ? `Chuyên đề: ${byId.get(chosen[0])!.name}` : chosen.length ? `Chuyên đề (${chosen.length})` : "Chuyên đề…";
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
        <OptionSelect
          className={sel}
          aria-label="Đợt kiểm tra"
          value={periodValue(value.semester_code, value.exam_kind)}
          onValueChange={(v) => {
            const p = parsePeriod(v);
            onChange({ semester_code: p.semester_code ?? null, exam_kind: p.exam_kind ?? null });
          }}
          emptyLabel="Mọi đợt kiểm tra"
          options={periodOptions(true)}
        />
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
        <Button variant={chosen.length ? "secondary" : "outline"} size="sm" className="h-8 max-w-72" onClick={() => setPicking(true)} data-testid="topic-filter">
          <Network /> <span className="truncate">{topicText}</span>
        </Button>
        {chosen.length > 0 && (
          <Button variant="ghost" size="icon-sm" onClick={() => onChange({ topic_ids: null, topic_id: null })} aria-label="Bỏ lọc chuyên đề">
            <X />
          </Button>
        )}
      </div>
      {chosen.length > 0 && (
        <p className="text-xs text-muted-foreground">Gồm cả các nhánh con của: {chosen.map((id) => topicLabel(byId.get(id)!, byId)).join("; ")}</p>
      )}
      <FormDialog open={picking} title="Lọc theo chuyên đề" onOpenChange={setPicking}>
        <TopicTreeSelect
          topics={topics}
          value={chosen}
          onCancel={() => setPicking(false)}
          onApply={(ids) => {
            setPicking(false);
            onChange({ topic_ids: ids.length ? ids.join(",") : null, topic_id: null });
          }}
        />
      </FormDialog>
    </div>
  );
}
