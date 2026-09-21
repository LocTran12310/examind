"use client";

import { useState } from "react";
import { Button, Input, Modal, Select } from "@/components/ui";
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
        <Button type="submit">Tìm</Button>
      </form>
      <div className="flex flex-wrap gap-2">
        <Select aria-label="Môn" value={value.subject_id ?? ""} onChange={(e) => set("subject_id", e.target.value)}>
          <option value="">Mọi môn</option>
          {taxonomy.subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select aria-label="Lớp" value={value.grade ?? ""} onChange={(e) => set("grade", e.target.value)}>
          <option value="">Mọi lớp</option>
          {taxonomy.grades.map((g) => (
            <option key={g.id} value={g.level}>
              {g.name}
            </option>
          ))}
        </Select>
        <Select aria-label="Học kỳ" value={value.semester_code ?? ""} onChange={(e) => set("semester_code", e.target.value)}>
          <option value="">Mọi học kỳ</option>
          {taxonomy.semesters.map((s) => (
            <option key={s.id} value={s.code}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select aria-label="Loại đề" value={value.exam_kind ?? ""} onChange={(e) => set("exam_kind", e.target.value)}>
          <option value="">Mọi loại đề</option>
          {EXAM_KINDS.map((k) => (
            <option key={k}>{k}</option>
          ))}
        </Select>
        <Select aria-label="Loại câu" value={value.type ?? ""} onChange={(e) => set("type", e.target.value)}>
          <option value="">Mọi loại câu</option>
          {Object.entries(TYPE_LABEL).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
        <Select aria-label="Mức độ" value={value.difficulty ?? ""} onChange={(e) => set("difficulty", e.target.value)}>
          <option value="">Mọi mức độ</option>
          {Object.entries(DIFFICULTY_LABEL).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
        <Select aria-label="Trạng thái" value={value.status ?? "usable"} onChange={(e) => set("status", e.target.value)}>
          <option value="usable">Dùng được</option>
          <option value="all">Tất cả</option>
          {Object.entries(STATUS_LABEL).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
        <Select aria-label="Tag" value={value.tag_ids ?? ""} onChange={(e) => set("tag_ids", e.target.value)}>
          <option value="">Mọi tag</option>
          {tags.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </Select>
        <Button onClick={() => setPicking(true)} data-testid="topic-filter">
          {topic ? `Chuyên đề: ${topic.name}` : "Chuyên đề…"}
        </Button>
        {topic && (
          <Button variant="ghost" onClick={() => set("topic_id", "")} aria-label="Bỏ lọc chuyên đề">
            ✕
          </Button>
        )}
      </div>
      {topic && <p className="text-xs text-gray-500">Gồm cả các nhánh con của {topicLabel(topic, byId)}</p>}
      <Modal open={picking} title="Lọc theo chuyên đề" onClose={() => setPicking(false)}>
        <TopicPicker
          topics={topics}
          onPick={(t) => {
            setPicking(false);
            set("topic_id", t.id);
          }}
          onClose={() => setPicking(false)}
        />
      </Modal>
    </div>
  );
}
