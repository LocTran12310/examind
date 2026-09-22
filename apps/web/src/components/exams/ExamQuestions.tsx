"use client";

import { ArrowDown, ArrowUp, ArrowUpDown, GripVertical, Save } from "lucide-react";
import { useMemo, useState } from "react";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Markdown } from "@/components/question/Markdown";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TYPE_LABEL, type ExamQuestion } from "@/lib/types";

const SECTION_LABEL: Record<string, string> = { I: "Phần I", II: "Phần II", III: "Phần III", IV: "Phần IV" };

/** Swap two ids in a list (the "Đổi chỗ với câu …" choice). */
export function swapped(ids: string[], a: string, b: string): string[] {
  const i = ids.indexOf(a), j = ids.indexOf(b);
  if (i < 0 || j < 0) return ids;
  const out = [...ids];
  [out[i], out[j]] = [out[j], out[i]];
  return out;
}

/** Move `id` to where `before` is (drag and drop). */
export function movedTo(ids: string[], id: string, before: string): string[] {
  if (id === before) return ids;
  const out = ids.filter((x) => x !== id);
  out.splice(out.indexOf(before) + (ids.indexOf(id) < ids.indexOf(before) ? 1 : 0), 0, id);
  return out;
}

export function ExamQuestions({
  questions,
  onSaveOrder,
  onSwap,
  onRemove,
  onPoints,
}: {
  questions: ExamQuestion[];
  /** the new order of every question, saved once */
  onSaveOrder: (ids: string[]) => Promise<void> | void;
  onSwap: (id: string) => void;
  onRemove: (id: string) => void;
  onPoints: (id: string, points: number) => void;
}) {
  const [order, setOrder] = useState<string[] | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const byId = useMemo(() => new Map(questions.map((q) => [q.id, q])), [questions]);
  const original = questions.map((q) => q.id);

  if (order) {
    const list = order.map((id) => byId.get(id)!).filter(Boolean);
    const changed = order.filter((id, i) => id !== original[i]).length;
    const sectionOf = (id: string) => byId.get(id)?.section;
    let last = "";
    return (
      <div className="grid gap-2" data-testid="exam-order">
        <div className="sticky top-0 z-10 flex flex-wrap items-center gap-2 rounded-lg border bg-card p-2 text-sm shadow-sm">
          <span className="text-muted-foreground">Kéo thả, dùng ↑/↓ hoặc chọn “Đổi chỗ với” — lưu một lần khi xong.</span>
          <div className="ml-auto flex gap-2">
            <Button size="sm" variant="outline" onClick={() => setOrder(null)} disabled={saving}>
              Hủy
            </Button>
            <Button
              size="sm"
              disabled={!changed || saving}
              onClick={async () => {
                setSaving(true);
                try {
                  await onSaveOrder(order);
                  setOrder(null);
                } finally {
                  setSaving(false);
                }
              }}
            >
              <Save /> Lưu thứ tự{changed ? ` (${changed} vị trí đổi)` : ""}
            </Button>
          </div>
        </div>
        <ol className="grid gap-1">
          {list.map((q, i) => {
            const header = q.section !== last;
            last = q.section;
            const peers = list.filter((x) => x.section === q.section);
            const k = peers.indexOf(q);
            const moved = original[i] !== q.id;
            return (
              <li key={q.id}>
                {header && <h3 className="mt-2 mb-1 text-sm font-semibold text-muted-foreground">{SECTION_LABEL[q.section] ?? q.section}</h3>}
                <div
                  draggable
                  onDragStart={() => setDragging(q.id)}
                  onDragEnd={() => setDragging(null)}
                  onDragOver={(e) => dragging && sectionOf(dragging) === q.section && e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (dragging && sectionOf(dragging) === q.section) setOrder(movedTo(order, dragging, q.id));
                    setDragging(null);
                  }}
                  className={cn("flex items-center gap-2 rounded-md border bg-card px-2 py-1", moved && "border-primary/60 bg-primary/5", dragging === q.id && "opacity-50")}
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
                    onValueChange={(v) => v && setOrder(swapped(order, q.id, v))}
                  />
                  <Button size="icon-xs" variant="ghost" aria-label={`Đưa câu ${i + 1} lên`} disabled={k === 0} onClick={() => setOrder(swapped(order, q.id, peers[k - 1].id))}>
                    <ArrowUp />
                  </Button>
                  <Button size="icon-xs" variant="ghost" aria-label={`Đưa câu ${i + 1} xuống`} disabled={k === peers.length - 1} onClick={() => setOrder(swapped(order, q.id, peers[k + 1].id))}>
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
          <Button size="sm" variant="outline" onClick={() => setOrder(original)}>
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

export function moved(ids: string[], id: string, delta: -1 | 1): string[] {
  const i = ids.indexOf(id);
  const j = i + delta;
  if (i < 0 || j < 0 || j >= ids.length) return ids;
  const out = [...ids];
  [out[i], out[j]] = [out[j], out[i]];
  return out;
}
