"use client";

import { useState } from "react";
import { TopicPicker, topicLabel } from "@/components/bank/TopicPicker";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormDialog } from "@/components/app/FormDialog";
import { OptionSelect } from "@/components/app/OptionSelect";
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
          <div key={i} className="flex flex-wrap items-center gap-2 rounded-lg border border-border p-2" data-testid={`row-${i}`}>
            <Button variant="outline" size="sm" onClick={() => setPicking(i)}>
              {r.topic_id && byId.get(r.topic_id) ? topicLabel(byId.get(r.topic_id)!, byId) : "Chọn chuyên đề…"}
            </Button>
            <OptionSelect
              aria-label="Tag"
              className="w-36"
              value={r.tag_id ?? ""}
              onValueChange={(v) => set(i, { tag_id: v || null })}
              emptyLabel="hoặc tag…"
              options={tags.map((t) => ({ value: t.id, label: t.name }))}
            />
            <OptionSelect
              aria-label="Loại câu"
              className="w-40"
              value={r.type}
              onValueChange={(v) => set(i, { type: v as BlueprintRow["type"] })}
              options={Object.entries(TYPE_LABEL).map(([k, v]) => ({ value: k, label: v }))}
            />
            <OptionSelect
              aria-label="Mức độ"
              className="w-36"
              value={r.difficulty ?? ""}
              onValueChange={(v) => set(i, { difficulty: (v || null) as BlueprintRow["difficulty"] })}
              emptyLabel="Mọi mức độ"
              options={Object.entries(DIFFICULTY_LABEL).map(([k, v]) => ({ value: k, label: v }))}
            />
            <Input aria-label="Số câu" type="number" min={1} max={200} className="w-20" value={r.count} onChange={(e) => set(i, { count: Number(e.target.value) })} />
            <Button size="sm" variant="ghost" onClick={() => setRows(rows.filter((_, j) => j !== i))} aria-label="Xóa dòng">
              ✕
            </Button>
            {miss && <span className="text-sm text-amber-700 dark:text-amber-400">thiếu {miss.missing} câu</span>}
          </div>
        );
      })}
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outline" onClick={() => setRows([...rows, { type: "mcq", count: 5 }])}>+ Thêm dòng</Button>
        <span className="text-sm text-muted-foreground">Tổng {total} câu</span>
        <Button className="ml-auto" disabled={invalid} onClick={() => onGenerate(rows)}>
          Tạo đề theo ma trận
        </Button>
      </div>
      {invalid && <FormAlert kind="warning">Mỗi dòng cần chuyên đề hoặc tag và số câu.</FormAlert>}
      <FormDialog open={picking !== null} title="Chọn chuyên đề (gồm nhánh con)" onOpenChange={(o) => !o && setPicking(null)}>
        <TopicPicker
          topics={topics}
          onPick={(t) => {
            if (picking !== null) set(picking, { topic_id: t.id });
            setPicking(null);
          }}
          onClose={() => setPicking(null)}
        />
      </FormDialog>
    </div>
  );
}
