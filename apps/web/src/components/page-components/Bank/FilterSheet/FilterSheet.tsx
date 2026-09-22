"use client";

import { Label } from "@/components/ui/label";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { TopicTreeSelect } from "@/components/common/TopicTreeSelect/TopicTreeSelect";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { DIFFICULTY_LABEL, STATUS_LABEL, TYPE_LABEL } from "@/constants/question.constant";
import { TAG_GROUP_LABEL } from "@/constants/tag.constant";
import { useFilterSheet } from "@/hooks/page-hooks/bank/use-filter-sheet";
import type { BankFacets } from "@/interfaces/question.interface";
import type { Tag } from "@/interfaces/tag.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { periodValue, parsePeriod } from "@/lib/common/exam-period";
import type { BankQuery, Changes } from "@/lib/page-libs/bank/filters";
import { cn } from "@/lib/utils";

type Option = { value: string; label: string; count?: number };

/** "Bộ lọc": every filter of the chosen subject with counts; edits a draft, applied at once (A-04, A-05). */
export function FilterSheet({
  open,
  onOpenChange,
  value,
  onApply,
  subjectName,
  taxonomy,
  topics,
  tags,
  facets,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  value: BankQuery;
  onApply: (changes: Changes) => void;
  subjectName?: string;
  taxonomy: Taxonomy;
  topics: Topic[];
  tags: Tag[];
  facets?: BankFacets | null;
}) {
  const { draft, set, topicIds, tagIds, toggleTag, sources, others, count, years, periods, changed, clearDraft, apply } = useFilterSheet({ open, value, tags, facets, onApply, onOpenChange });

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="gap-0 p-0 data-[side=right]:w-full data-[side=right]:sm:max-w-md" data-testid="filter-sheet">
        <SheetHeader className="border-b">
          <SheetTitle>Bộ lọc{subjectName ? ` · ${subjectName}` : ""}</SheetTitle>
          <SheetDescription>Chỉ hiện chuyên đề và tag của môn đang chọn. Số bên phải là số câu phù hợp.</SheetDescription>
        </SheetHeader>
        <div className="min-h-0 flex-1 divide-y overflow-y-auto">
          <Section title="Chuyên đề" active={topicIds.length} defaultOpen>
            {topics.length ? (
              <TopicTreeSelect key={open ? "open" : "closed"} topics={topics} value={topicIds} counts={facets?.topics} onChange={(ids) => set({ topic_ids: ids.join(",") || null, topic_id: null })} />
            ) : (
              <p className="text-sm text-muted-foreground">Môn này chưa có cây chuyên đề.</p>
            )}
          </Section>
          <Section title="Loại câu" active={draft.type ? 1 : 0} defaultOpen>
            <Choices
              label="Loại câu"
              value={draft.type}
              onChange={(v) => set({ type: v })}
              options={Object.entries(TYPE_LABEL).map(([v, l]) => ({ value: v, label: l, count: count(facets?.types, v) }))}
            />
          </Section>
          <Section title="Mức độ" active={draft.difficulty ? 1 : 0}>
            <Choices
              label="Mức độ"
              value={draft.difficulty}
              onChange={(v) => set({ difficulty: v })}
              options={Object.entries(DIFFICULTY_LABEL).map(([v, l]) => ({ value: v, label: l, count: count(facets?.difficulties, v) }))}
            />
          </Section>
          <Section title="Lớp" active={draft.grade ? 1 : 0}>
            <Choices
              label="Lớp"
              value={draft.grade}
              onChange={(v) => set({ grade: v })}
              options={taxonomy.grades.map((g) => ({ value: String(g.level), label: g.name, count: count(facets?.grades, String(g.level)) }))}
            />
          </Section>
          <Section title="Đợt kiểm tra" active={draft.semester_code || draft.exam_kind ? 1 : 0} defaultOpen>
            <Choices
              label="Đợt kiểm tra"
              value={periodValue(draft.semester_code, draft.exam_kind) || undefined}
              onChange={(v) => {
                const p = v ? parsePeriod(v) : { semester_code: undefined, exam_kind: undefined };
                set({ semester_code: p.semester_code ?? null, exam_kind: p.exam_kind ?? null });
              }}
              options={periods.map((o) => ({ value: o.value, label: o.label, count: count(facets?.periods, o.value) }))}
              empty="Chưa có câu nào gắn đợt kiểm tra."
            />
          </Section>
          <Section title="Năm học" active={draft.school_year ? 1 : 0}>
            <Choices
              label="Năm học"
              value={draft.school_year}
              onChange={(v) => set({ school_year: v })}
              options={years.map((y) => ({ value: y, label: y, count: count(facets?.school_years, y) }))}
              empty="Chưa có câu nào từ đề có năm học."
            />
          </Section>
          <Section title="Nguồn đề" active={sources.filter((t) => tagIds.includes(t.id)).length} defaultOpen={sources.length > 0}>
            <TagChecks tags={sources} checked={tagIds} onToggle={toggleTag} counts={facets?.tags} empty="Chưa có nguồn đề." />
          </Section>
          <Section title="Tags" active={others.filter((t) => tagIds.includes(t.id)).length}>
            {(["method", "skill", "custom"] as const).map((g) => {
              const group = others.filter((t) => t.group === g);
              return group.length ? (
                <div key={g} className="mb-2">
                  <p className="mb-1 text-xs font-medium text-muted-foreground">{TAG_GROUP_LABEL[g]}</p>
                  <TagChecks tags={group} checked={tagIds} onToggle={toggleTag} counts={facets?.tags} />
                </div>
              ) : null;
            })}
            {!others.length && <p className="text-sm text-muted-foreground">Môn này chưa có tag.</p>}
          </Section>
          <Section title="Trạng thái" active={draft.status && draft.status !== "usable" ? 1 : 0}>
            <Choices
              label="Trạng thái"
              value={draft.status && draft.status !== "usable" ? draft.status : undefined}
              onChange={(v) => set({ status: v })}
              options={[{ value: "all", label: "Mọi trạng thái" }, ...Object.entries(STATUS_LABEL as Record<string, string>).map(([v, l]) => ({ value: v, label: l }))]}
              noneLabel="Dùng được"
            />
          </Section>
        </div>
        <SheetFooter className="flex-row justify-between border-t">
          <Button variant="ghost" onClick={clearDraft}>
            Xóa lọc
          </Button>
          <Button onClick={apply}>Áp dụng{changed.length ? ` (${changed.length})` : ""}</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

function Section({ title, active, defaultOpen, children }: { title: string; active: number; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(!!defaultOpen || active > 0);
  return (
    <Collapsible open={open} onOpenChange={setOpen} className="px-4 py-2">
      <CollapsibleTrigger className="flex w-full items-center gap-2 py-1.5 text-sm font-medium">
        <span>{title}</span>
        {active > 0 && <Badge className="h-4 px-1.5">{active}</Badge>}
        <ChevronDown className={cn("ml-auto size-4 text-muted-foreground transition-transform", open && "rotate-180")} />
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-1 pb-2">{children}</CollapsibleContent>
    </Collapsible>
  );
}

/** Single choice shown as pills with counts; the chosen one again = none. */
function Choices({ label, value, onChange, options, empty, noneLabel }: { label: string; value?: string; onChange: (v: string | null) => void; options: Option[]; empty?: string; noneLabel?: string }) {
  if (!options.length) return <p className="text-sm text-muted-foreground">{empty}</p>;
  return (
    <div className="flex flex-wrap gap-1.5" role="group" aria-label={label}>
      {noneLabel && (
        <Pill pressed={!value} onClick={() => onChange(null)}>
          {noneLabel}
        </Pill>
      )}
      {options.map((o) => (
        <Pill key={o.value} pressed={value === o.value} dim={o.count === 0 && value !== o.value} onClick={() => onChange(value === o.value ? null : o.value)}>
          {o.label}
          {o.count !== undefined && <span className="tabular-nums opacity-70">{o.count}</span>}
        </Pill>
      ))}
    </div>
  );
}

function Pill({ pressed, dim, onClick, children }: { pressed: boolean; dim?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <Button type="button" size="xs" variant={pressed ? "default" : "outline"} aria-pressed={pressed} className={cn("gap-1.5 rounded-full", dim && "opacity-50")} onClick={onClick}>
      {children}
    </Button>
  );
}

function TagChecks({ tags, checked, onToggle, counts, empty }: { tags: Tag[]; checked: string[]; onToggle: (id: string) => void; counts?: Record<string, number>; empty?: string }) {
  if (!tags.length) return empty ? <p className="text-sm text-muted-foreground">{empty}</p> : null;
  return (
    <ul className="grid gap-0.5">
      {tags.map((t) => (
        <li key={t.id}>
          <Label className="cursor-pointer rounded-md px-1 py-0.5 font-normal leading-normal hover:bg-muted/60">
            <Checkbox checked={checked.includes(t.id)} onCheckedChange={() => onToggle(t.id)} aria-label={t.name} />
            <span className="min-w-0 flex-1 truncate">{t.name}</span>
            <span className="text-xs tabular-nums text-muted-foreground">{counts?.[t.id] ?? 0}</span>
          </Label>
        </li>
      ))}
    </ul>
  );
}
