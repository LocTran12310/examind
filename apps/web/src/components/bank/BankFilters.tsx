"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormDialog } from "@/components/app/FormDialog";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { DIFFICULTY_LABEL, EXAM_KINDS, STATUS_LABEL, TYPE_LABEL, type Tag, type Taxonomy, type Topic } from "@/lib/types";
import { TopicPicker, topicLabel } from "./TopicPicker";

export type BankQuery = Record<string, string>;

export function BankFilters({
  value,
  onChange,
  taxonomy,
  topics,
  tags,
}: {
  value: BankQuery;
  onChange: (v: BankQuery) => void;
  taxonomy: Taxonomy;
  topics: Topic[];
  tags: Tag[];
}) {
  const [text, setText] = useState(value.q ?? "");
  const [picking, setPicking] = useState(false);
  const set = (k: string, v: string) => onChange({ ...value, [k]: v, page: "1" });
  const byId = new Map(topics.map((t) => [t.id, t]));
  const topic = value.topic_id ? byId.get(value.topic_id) : undefined;
  return (
    <div className="mb-4 space-y-3" data-testid="bank-filters">
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          set("q", text);
        }}
      >
        <Input placeholder="Tìm nội dung câu hỏi (không cần dấu)…" value={text} onChange={(e) => setText(e.target.value)} />
        <Button variant="outline" type="submit">Tìm</Button>
      </form>
      <div className="flex flex-wrap gap-2">
        <NativeSelect aria-label="Môn" value={value.subject_id ?? ""} onChange={(e) => set("subject_id", e.target.value)}>
          <NativeSelectOption value="">Mọi môn</NativeSelectOption>
          {taxonomy.subjects.map((s) => (
            <NativeSelectOption key={s.id} value={s.id}>
              {s.name}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <NativeSelect aria-label="Lớp" value={value.grade ?? ""} onChange={(e) => set("grade", e.target.value)}>
          <NativeSelectOption value="">Mọi lớp</NativeSelectOption>
          {taxonomy.grades.map((g) => (
            <NativeSelectOption key={g.id} value={g.level}>
              {g.name}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <NativeSelect aria-label="Học kỳ" value={value.semester_code ?? ""} onChange={(e) => set("semester_code", e.target.value)}>
          <NativeSelectOption value="">Mọi học kỳ</NativeSelectOption>
          {taxonomy.semesters.map((s) => (
            <NativeSelectOption key={s.id} value={s.code}>
              {s.name}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <NativeSelect aria-label="Loại đề" value={value.exam_kind ?? ""} onChange={(e) => set("exam_kind", e.target.value)}>
          <NativeSelectOption value="">Mọi loại đề</NativeSelectOption>
          {EXAM_KINDS.map((k) => (
            <NativeSelectOption key={k}>{k}</NativeSelectOption>
          ))}
        </NativeSelect>
        <NativeSelect aria-label="Loại câu" value={value.type ?? ""} onChange={(e) => set("type", e.target.value)}>
          <NativeSelectOption value="">Mọi loại câu</NativeSelectOption>
          {Object.entries(TYPE_LABEL).map(([k, v]) => (
            <NativeSelectOption key={k} value={k}>
              {v}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <NativeSelect aria-label="Mức độ" value={value.difficulty ?? ""} onChange={(e) => set("difficulty", e.target.value)}>
          <NativeSelectOption value="">Mọi mức độ</NativeSelectOption>
          {Object.entries(DIFFICULTY_LABEL).map(([k, v]) => (
            <NativeSelectOption key={k} value={k}>
              {v}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <NativeSelect aria-label="Trạng thái" value={value.status ?? "usable"} onChange={(e) => set("status", e.target.value)}>
          <NativeSelectOption value="usable">Dùng được</NativeSelectOption>
          <NativeSelectOption value="all">Tất cả</NativeSelectOption>
          {Object.entries(STATUS_LABEL).map(([k, v]) => (
            <NativeSelectOption key={k} value={k}>
              {v}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <NativeSelect aria-label="Tag" value={value.tag_ids ?? ""} onChange={(e) => set("tag_ids", e.target.value)}>
          <NativeSelectOption value="">Mọi tag</NativeSelectOption>
          {tags.map((t) => (
            <NativeSelectOption key={t.id} value={t.id}>
              {t.name}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <Button variant="outline" onClick={() => setPicking(true)} data-testid="topic-filter">
          {topic ? `Chuyên đề: ${topic.name}` : "Chuyên đề…"}
        </Button>
        {topic && (
          <Button variant="ghost" onClick={() => set("topic_id", "")} aria-label="Bỏ lọc chuyên đề">
            ✕
          </Button>
        )}
      </div>
      {topic && <p className="text-xs text-muted-foreground">Gồm cả các nhánh con của {topicLabel(topic, byId)}</p>}
      <FormDialog open={picking} title="Lọc theo chuyên đề" onOpenChange={(o) => !o && setPicking(false)}>
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
