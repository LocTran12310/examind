"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { FormDialog } from "@/components/app/FormDialog";
import { OptionSelect } from "@/components/app/OptionSelect";
import { TopicPicker } from "@/components/common/TopicPicker/TopicPicker";
import { topicLabel } from "@/components/topics/tree";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DIFFICULTY_LABEL, TYPE_LABEL } from "@/constants/question.constant";
import { useBlueprintEditor } from "@/hooks/page-hooks/exam-detail/use-blueprint-editor";
import type { BlueprintRow, BlueprintShortfall } from "@/interfaces/exam.interface";
import type { Tag } from "@/interfaces/tag.interface";
import type { Topic } from "@/interfaces/topic.interface";

export interface BlueprintEditorProps {
  initial: BlueprintRow[];
  topics: Topic[];
  tags: Tag[];
  shortfalls: BlueprintShortfall[];
  onGenerate: (rows: BlueprintRow[]) => void;
}

export function BlueprintEditor({ initial, topics, tags, shortfalls, onGenerate }: BlueprintEditorProps) {
  const b = useBlueprintEditor(initial, topics);
  return (
    <div className="space-y-3" data-testid="blueprint">
      {b.rows.map((r, i) => {
        const miss = shortfalls.find((s) => s.row === i);
        const topic = r.topic_id ? b.byId.get(r.topic_id) : undefined;
        return (
          <div key={i} className="flex flex-wrap items-center gap-2 rounded-lg border border-border p-2" data-testid={`row-${i}`}>
            <Button variant="outline" size="sm" onClick={() => b.setPicking(i)}>
              {topic ? topicLabel(topic, b.byId) : "Chọn chuyên đề…"}
            </Button>
            <OptionSelect
              aria-label="Tag"
              className="w-36"
              value={r.tag_id ?? ""}
              onValueChange={(v) => b.set(i, { tag_id: v || null })}
              emptyLabel="hoặc tag…"
              options={tags.map((t) => ({ value: t.id, label: t.name }))}
            />
            <OptionSelect
              aria-label="Loại câu"
              className="w-40"
              value={r.type}
              onValueChange={(v) => b.set(i, { type: v as BlueprintRow["type"] })}
              options={Object.entries(TYPE_LABEL).map(([k, v]) => ({ value: k, label: v }))}
            />
            <OptionSelect
              aria-label="Mức độ"
              className="w-36"
              value={r.difficulty ?? ""}
              onValueChange={(v) => b.set(i, { difficulty: (v || null) as BlueprintRow["difficulty"] })}
              emptyLabel="Mọi mức độ"
              options={Object.entries(DIFFICULTY_LABEL).map(([k, v]) => ({ value: k, label: v }))}
            />
            <Input aria-label="Số câu" type="number" min={1} max={200} className="w-20" value={r.count} onChange={(e) => b.set(i, { count: Number(e.target.value) })} />
            <Button size="sm" variant="ghost" onClick={() => b.removeRow(i)} aria-label="Xóa dòng">
              ✕
            </Button>
            {miss && <span className="text-sm text-amber-700 dark:text-amber-400">thiếu {miss.missing} câu</span>}
          </div>
        );
      })}
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outline" onClick={b.addRow}>
          + Thêm dòng
        </Button>
        <span className="text-sm text-muted-foreground">Tổng {b.total} câu</span>
        <Button className="ml-auto" disabled={b.invalid} onClick={() => onGenerate(b.rows)}>
          Tạo đề theo ma trận
        </Button>
      </div>
      {b.invalid && <FormAlert kind="warning">Mỗi dòng cần chuyên đề hoặc tag và số câu.</FormAlert>}
      <FormDialog open={b.picking !== null} title="Chọn chuyên đề (gồm nhánh con)" onOpenChange={(o) => !o && b.setPicking(null)}>
        <TopicPicker topics={topics} onPick={(t) => b.pick(t.id)} onClose={() => b.setPicking(null)} />
      </FormDialog>
    </div>
  );
}
