"use client";

import { Markdown } from "@/components/question/Markdown";
import { Badge, Button, Input } from "@/components/ui";
import { TYPE_LABEL, type ExamQuestion } from "@/lib/types";

export function ExamQuestions({
  questions,
  onMove,
  onSwap,
  onRemove,
  onPoints,
}: {
  questions: ExamQuestion[];
  onMove: (id: string, delta: -1 | 1) => void;
  onSwap: (id: string) => void;
  onRemove: (id: string) => void;
  onPoints: (id: string, points: number) => void;
}) {
  let lastSection = "";
  return (
    <ol className="space-y-2" data-testid="exam-questions">
      {questions.map((q, i) => {
        const header = q.section !== lastSection;
        lastSection = q.section;
        return (
          <li key={q.id}>
            {header && <h3 className="mb-1 mt-3 text-sm font-semibold text-gray-600">Phần {q.section}</h3>}
            <div className="flex gap-3 rounded-lg border border-gray-200 bg-white p-3" data-testid={`eq-${q.position}`}>
              <span className="w-8 shrink-0 font-semibold">{q.position}.</span>
              <div className="min-w-0 flex-1 text-sm">
                <div className="line-clamp-3">
                  <Markdown>{q.stem}</Markdown>
                </div>
                <div className="mt-1 flex flex-wrap gap-1 text-xs">
                  <Badge>{TYPE_LABEL[q.type]}</Badge>
                  {q.topics[0] && <span className="rounded bg-brand-50 px-2 py-0.5 text-brand-700">{q.topics[0].name}</span>}
                </div>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <label className="flex items-center gap-1 text-xs text-gray-500">
                  điểm
                  <Input
                    aria-label={`Điểm câu ${q.position}`}
                    type="number"
                    step="0.05"
                    min={0.05}
                    className="h-7 w-20"
                    defaultValue={q.points}
                    onBlur={(e) => Number(e.target.value) !== q.points && onPoints(q.id, Number(e.target.value))}
                  />
                </label>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" aria-label="Lên" disabled={i === 0} onClick={() => onMove(q.id, -1)}>
                    ↑
                  </Button>
                  <Button size="sm" variant="ghost" aria-label="Xuống" disabled={i === questions.length - 1} onClick={() => onMove(q.id, 1)}>
                    ↓
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => onSwap(q.id)}>
                    Đổi câu
                  </Button>
                  <Button size="sm" variant="ghost" className="text-red-700" onClick={() => onRemove(q.id)}>
                    Bỏ
                  </Button>
                </div>
              </div>
            </div>
          </li>
        );
      })}
    </ol>
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
