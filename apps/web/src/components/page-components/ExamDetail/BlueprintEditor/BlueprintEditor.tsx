"use client";

import { X } from "lucide-react";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { TopicPicker } from "@/components/common/TopicPicker/TopicPicker";
import { topicLabel } from "@/lib/common/topic-tree";
import { shortfallReason } from "@/lib/page-libs/exam-detail/blueprint";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SECTION_LABEL, SECTION_OF_TYPE } from "@/constants/exam.constant";
import { DIFFICULTY_LABEL, TYPE_LABEL } from "@/constants/question.constant";
import { useBlueprintEditor } from "@/hooks/page-hooks/exam-detail/use-blueprint-editor";
import type { BlueprintRefusal, BlueprintRow, BlueprintShortfall } from "@/interfaces/exam.interface";
import type { QuestionType } from "@/interfaces/question.interface";
import type { Tag } from "@/interfaces/tag.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { cn } from "@/lib/utils";

export interface BlueprintEditorProps {
  initial: BlueprintRow[];
  topics: Topic[];
  tags: Tag[];
  /** the exam's subject: what the counts beside a topic are counted in (ADR-01) */
  subjectId: string | null;
  shortfalls: BlueprintShortfall[];
  /** the row the server refused because its topic holds nothing (AC-06) */
  refusal: BlueprintRefusal | null;
  onEdit: () => void;
  onGenerate: (rows: BlueprintRow[]) => void;
}

/** The exam matrix. One row is one line at desktop width and a deliberate two-column stack below it;
 *  each row says how many questions its own filters select — the pool the generator will draw from, not an
 *  approximation of it (blueprint-truth ADR-01) — so a row that cannot be filled is visible before generating.
 *  The row names the topic itself and keeps the whole path in the tooltip — the line is narrow. */
export function BlueprintEditor({ initial, topics, tags, subjectId, shortfalls, refusal, onEdit, onGenerate }: BlueprintEditorProps) {
  const b = useBlueprintEditor(initial, topics, subjectId, onEdit);
  return (
    <div className="space-y-3" data-testid="blueprint">
      {/* The part is not a choice in this matrix — it is read off each question's type — so a paper with three
          parts is three rows. Said here because the screen otherwise shows only the consequence: "Thang điểm của
          đề" listing three parts beside a matrix of one row, which reads as two numbers that disagree. Built from
          the same map the server sections by, so it cannot drift from what generating actually does. */}
      <p className="text-sm text-muted-foreground" data-testid="blueprint-parts">
        Phần của đề theo loại câu: {(Object.keys(TYPE_LABEL) as QuestionType[]).map((t) => `${TYPE_LABEL[t]} → ${SECTION_LABEL[SECTION_OF_TYPE[t]]}`).join(" · ")}. Đề nhiều
        phần thì mỗi loại một dòng; dòng “Mọi loại” bốc lẫn các loại.
      </p>
      {b.rows.map((r, i) => {
        const miss = shortfalls.find((s) => s.row === i);
        const topic = r.topic_id ? b.byId.get(r.topic_id) : undefined;
        const held = b.held(r);
        const matching = b.matching(i);
        const empty = held === 0;
        // the row's own pool is smaller than what it asks for, which is known before generating now (AC-03);
        // once the server has answered, its count is the authority — it also knows what the other rows took.
        // An empty topic says so in red already, and repeating it as a shortfall would add nothing.
        const missing = miss ? miss.missing : !empty && matching !== null && matching < r.count ? r.count - matching : 0;
        const refused = refusal?.row === i;
        return (
          <div
            key={i}
            className={cn(
              "grid grid-cols-2 items-center gap-2 rounded-lg border p-2 lg:grid-cols-[minmax(0,1fr)_6.5rem_7rem_6.5rem_4rem_auto]",
              refused || empty ? "border-destructive/60" : "border-border",
            )}
            data-testid={`row-${i}`}
          >
            <Button variant="outline" size="sm" className="col-span-2 min-w-0 justify-start lg:col-span-1" title={topic ? topicLabel(topic, b.byId) : undefined} onClick={() => b.setPicking(i)}>
              <span className="truncate">{topic ? topic.name : "Chọn chuyên đề…"}</span>
              {matching !== null && <span className={cn("ml-auto shrink-0 text-xs tabular-nums", empty ? "text-destructive" : "text-muted-foreground")}>{matching} câu</span>}
            </Button>
            <OptionSelect
              aria-label="Tag"
              value={r.tag_id ?? ""}
              onValueChange={(v) => b.set(i, { tag_id: v || null })}
              emptyLabel="hoặc tag…"
              options={tags.map((t) => ({ value: t.id, label: t.name }))}
            />
            <OptionSelect
              aria-label="Loại câu"
              value={r.type ?? ""}
              onValueChange={(v) => b.set(i, { type: (v || null) as BlueprintRow["type"] })}
              emptyLabel="Mọi loại"
              options={Object.entries(TYPE_LABEL).map(([k, v]) => ({ value: k, label: v }))}
            />
            <OptionSelect
              aria-label="Mức độ"
              value={r.difficulty ?? ""}
              onValueChange={(v) => b.set(i, { difficulty: (v || null) as BlueprintRow["difficulty"] })}
              emptyLabel="Mọi mức độ"
              options={Object.entries(DIFFICULTY_LABEL).map(([k, v]) => ({ value: k, label: v }))}
            />
            <Input aria-label="Số câu" type="number" min={1} max={200} value={r.count} onChange={(e) => b.set(i, { count: Number(e.target.value) })} />
            <Button size="sm" variant="ghost" className="col-span-2 justify-self-end text-muted-foreground lg:col-span-1" onClick={() => b.removeRow(i)} aria-label="Xóa dòng">
              <X />
              <span className="lg:hidden">Xóa dòng</span>
            </Button>
            {(empty || missing > 0) && (
              <div className="col-span-2 flex flex-wrap gap-x-3 text-sm lg:col-span-6">
                {empty && (
                  <span className="text-destructive">
                    Chuyên đề “{topic ? topic.name : r.topic_id}” chưa có câu hỏi nào dùng được — chọn chuyên đề khác trước khi tạo đề.
                  </span>
                )}
                {missing > 0 && <span className="text-amber-700 dark:text-amber-400">{shortfallReason(r, held, matching, missing)}</span>}
              </div>
            )}
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
      {refusal && (
        <div data-testid="blueprint-refusal">
          <FormAlert>{refusal.message}</FormAlert>
        </div>
      )}
      <FormDialog open={b.picking !== null} title="Chọn chuyên đề (gồm nhánh con)" onOpenChange={(o) => !o && b.setPicking(null)}>
        <TopicPicker
          topics={topics}
          counts={b.counts}
          initial={b.picking !== null ? (b.rows[b.picking]?.topic_id ?? null) : null}
          onPick={(t) => b.pick(t.id)}
          onClose={() => b.setPicking(null)}
        />
      </FormDialog>
    </div>
  );
}
