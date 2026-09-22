"use client";

import { ArrowDown, ArrowUp, ArrowUpDown, GripVertical, Save } from "lucide-react";
import { OptionSelect } from "@/components/app/OptionSelect";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SECTION_LABEL } from "@/constants/exam.constant";
import { TYPE_LABEL } from "@/constants/question.constant";
import { useExamQuestions } from "@/hooks/page-hooks/exam-detail/use-exam-questions";
import type { ExamQuestion } from "@/interfaces/exam.interface";
import { cn } from "@/lib/utils";

export interface ExamQuestionsProps {
  questions: ExamQuestion[];
  /** the new order of every question, saved once */
  onSaveOrder: (ids: string[]) => Promise<void> | void;
  onSwap: (id: string) => void;
  onRemove: (id: string) => void;
  onPoints: (id: string, points: number) => void;
}

export function ExamQuestions({ questions, onSaveOrder, onSwap, onRemove, onPoints }: ExamQuestionsProps) {
  const o = useExamQuestions(questions, onSaveOrder);

  if (o.order) {
    const order = o.order;
    let last = "";
    return (
      <div className="grid gap-2" data-testid="exam-order">
        <div className="sticky top-0 z-10 flex flex-wrap items-center gap-2 rounded-lg border bg-card p-2 text-sm shadow-sm">
          <span className="text-muted-foreground">Kéo thả, dùng ↑/↓ hoặc chọn “Đổi chỗ với” — lưu một lần khi xong.</span>
          <div className="ml-auto flex gap-2">
            <Button size="sm" variant="outline" onClick={o.cancel} disabled={o.saving}>
              Hủy
            </Button>
            <Button size="sm" disabled={!o.changed || o.saving} onClick={() => void o.save()}>
              <Save /> Lưu thứ tự{o.changed ? ` (${o.changed} vị trí đổi)` : ""}
            </Button>
          </div>
        </div>
        <ol className="grid gap-1">
          {o.list.map((q, i) => {
            const header = q.section !== last;
            last = q.section;
            const peers = o.list.filter((x) => x.section === q.section);
            const k = peers.indexOf(q);
            const moved = o.original[i] !== q.id;
            return (
              <li key={q.id}>
                {header && <h3 className="mt-2 mb-1 text-sm font-semibold text-muted-foreground">{SECTION_LABEL[q.section] ?? q.section}</h3>}
                <div
                  draggable
                  onDragStart={() => o.setDragging(q.id)}
                  onDragEnd={() => o.setDragging(null)}
                  onDragOver={(e) => o.canDrop(q) && e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    o.drop(q);
                  }}
                  className={cn("flex items-center gap-2 rounded-md border bg-card px-2 py-1", moved && "border-primary/60 bg-primary/5", o.dragging === q.id && "opacity-50")}
                  data-testid={`order-${i + 1}`}
                >
                  <GripVertical className="size-4 shrink-0 cursor-grab text-muted-foreground" aria-hidden />
                  <span className="w-8 shrink-0 text-right font-semibold tabular-nums">{i + 1}.</span>
                  <div className="line-clamp-1 min-w-0 flex-1 text-sm">
                    <Markdown className="[&_img]:hidden [&_p]:my-0 [&_p]:inline">{q.stem}</Markdown>
                  </div>
                  <OptionSelect
                    size="sm"
                    className="h-7 w-36"
                    aria-label={`Đổi chỗ câu ${i + 1} với`}
                    value=""
                    emptyLabel="Đổi chỗ với…"
                    options={peers.filter((x) => x.id !== q.id).map((x) => ({ value: x.id, label: `Câu ${order.indexOf(x.id) + 1}` }))}
                    onValueChange={(v) => v && o.swap(q.id, v)}
                  />
                  <Button size="icon-xs" variant="ghost" aria-label={`Đưa câu ${i + 1} lên`} disabled={k === 0} onClick={() => o.swap(q.id, peers[k - 1].id)}>
                    <ArrowUp />
                  </Button>
                  <Button size="icon-xs" variant="ghost" aria-label={`Đưa câu ${i + 1} xuống`} disabled={k === peers.length - 1} onClick={() => o.swap(q.id, peers[k + 1].id)}>
                    <ArrowDown />
                  </Button>
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    );
  }

  let lastSection = "";
  return (
    <div className="grid gap-2">
      {questions.length > 1 && (
        <div className="flex justify-end">
          <Button size="sm" variant="outline" onClick={o.startOrdering}>
            <ArrowUpDown /> Sắp xếp thứ tự
          </Button>
        </div>
      )}
      <ol className="space-y-2" data-testid="exam-questions">
        {questions.map((q) => {
          const header = q.section !== lastSection;
          lastSection = q.section;
          return (
            <li key={q.id}>
              {header && <h3 className="mt-3 mb-1 text-sm font-semibold text-muted-foreground">{SECTION_LABEL[q.section] ?? q.section}</h3>}
              <div className="flex gap-3 rounded-lg border border-border bg-card p-3" data-testid={`eq-${q.position}`}>
                <span className="w-8 shrink-0 font-semibold">{q.position}.</span>
                <div className="min-w-0 flex-1 text-sm">
                  <div className="line-clamp-3">
                    <Markdown>{q.stem}</Markdown>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1 text-xs">
                    <ToneBadge>{TYPE_LABEL[q.type]}</ToneBadge>
                    {q.topics[0] && <ToneBadge tone="blue">{q.topics[0].name}</ToneBadge>}
                  </div>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Label htmlFor={`points-${q.id}`} className="text-xs font-normal text-muted-foreground">
                      điểm
                    </Label>
                    <Input
                      id={`points-${q.id}`}
                      aria-label={`Điểm câu ${q.position}`}
                      type="number"
                      step="0.05"
                      min={0.05}
                      className="h-7 w-20"
                      defaultValue={q.points}
                      onBlur={(e) => Number(e.target.value) !== q.points && onPoints(q.id, Number(e.target.value))}
                    />
                  </div>
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" onClick={() => onSwap(q.id)}>
                      Đổi câu
                    </Button>
                    <Button size="sm" variant="ghost" className="text-destructive" onClick={() => onRemove(q.id)}>
                      Bỏ
                    </Button>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
