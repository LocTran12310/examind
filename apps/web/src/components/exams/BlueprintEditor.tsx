"use client";

import { useState } from "react";
import { TopicPicker, topicLabel } from "@/components/bank/TopicPicker";
import { Alert, Button, Input, Modal, Select } from "@/components/ui";
import { DIFFICULTY_LABEL, TYPE_LABEL, type BlueprintRow, type Tag, type Topic } from "@/lib/types";

export function BlueprintEditor({
  initial,
  topics,
  tags,
  shortfalls,
  onGenerate,
}: {
  initial: BlueprintRow[];
  topics: Topic[];
  tags: Tag[];
  shortfalls: { row: number; missing: number }[];
  onGenerate: (rows: BlueprintRow[]) => void;
}) {
  const [rows, setRows] = useState<BlueprintRow[]>(initial.length ? initial : [{ type: "mcq", count: 10 }]);
  const [picking, setPicking] = useState<number | null>(null);
  const byId = new Map(topics.map((t) => [t.id, t]));
  const set = (i: number, patch: Partial<BlueprintRow>) => setRows(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const total = rows.reduce((n, r) => n + (r.count || 0), 0);
  const invalid = rows.some((r) => !(r.topic_id || r.tag_id) || !r.count);
  return (
    <div className="space-y-3" data-testid="blueprint">
      {rows.map((r, i) => {
        const miss = shortfalls.find((s) => s.row === i);
        return (
          <div key={i} className="flex flex-wrap items-center gap-2 rounded-lg border border-gray-200 p-2" data-testid={`row-${i}`}>
            <Button size="sm" onClick={() => setPicking(i)}>
              {r.topic_id && byId.get(r.topic_id) ? topicLabel(byId.get(r.topic_id)!, byId) : "Chọn chuyên đề…"}
            </Button>
            <Select aria-label="Tag" value={r.tag_id ?? ""} onChange={(e) => set(i, { tag_id: e.target.value || null })}>
              <option value="">hoặc tag…</option>
              {tags.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </Select>
            <Select aria-label="Loại câu" value={r.type} onChange={(e) => set(i, { type: e.target.value as BlueprintRow["type"] })}>
              {Object.entries(TYPE_LABEL).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
            <Select aria-label="Mức độ" value={r.difficulty ?? ""} onChange={(e) => set(i, { difficulty: e.target.value || null })}>
              <option value="">Mọi mức độ</option>
              {Object.entries(DIFFICULTY_LABEL).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
            <Input aria-label="Số câu" type="number" min={1} max={200} className="w-20" value={r.count} onChange={(e) => set(i, { count: Number(e.target.value) })} />
            <Button size="sm" variant="ghost" onClick={() => setRows(rows.filter((_, j) => j !== i))} aria-label="Xóa dòng">
              ✕
            </Button>
            {miss && <span className="text-sm text-amber-700">thiếu {miss.missing} câu</span>}
          </div>
        );
      })}
      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={() => setRows([...rows, { type: "mcq", count: 5 }])}>+ Thêm dòng</Button>
        <span className="text-sm text-gray-500">Tổng {total} câu</span>
        <Button variant="primary" className="ml-auto" disabled={invalid} onClick={() => onGenerate(rows)}>
          Tạo đề theo ma trận
        </Button>
      </div>
      {invalid && <Alert tone="amber">Mỗi dòng cần chuyên đề hoặc tag và số câu.</Alert>}
      <Modal open={picking !== null} title="Chọn chuyên đề (gồm nhánh con)" onClose={() => setPicking(null)}>
        <TopicPicker
          topics={topics}
          onPick={(t) => {
            if (picking !== null) set(picking, { topic_id: t.id });
            setPicking(null);
          }}
          onClose={() => setPicking(null)}
        />
      </Modal>
    </div>
  );
}
