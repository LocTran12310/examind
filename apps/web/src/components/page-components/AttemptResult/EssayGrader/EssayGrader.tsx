"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useEssayGrader } from "@/hooks/page-hooks/attempt-result/use-essay-grader";

export interface EssayGraderProps {
  attemptId: string;
  questionId: string;
  max: number;
  points: number | null;
  comment: string | null;
}

export function EssayGrader({ attemptId, questionId, max, points, comment }: EssayGraderProps) {
  const g = useEssayGrader(attemptId, questionId, points, comment);
  return (
    <div className="mt-3 space-y-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3" data-testid="essay-grader">
      <div className="flex items-center gap-2 text-sm">
        <span>Chấm điểm</span>
        <Input aria-label="Điểm tự luận" type="number" step="0.25" min={0} max={max} className="h-8 w-24" value={g.points} onChange={(e) => g.setPoints(e.target.value)} />
        <span className="text-muted-foreground">/ {max}</span>
      </div>
      <Textarea aria-label="Nhận xét" rows={2} placeholder="Nhận xét cho học sinh" value={g.comment} onChange={(e) => g.setComment(e.target.value)} />
      {g.error && <FormAlert>{g.error}</FormAlert>}
      <Button size="sm" onClick={g.save}>
        Lưu điểm
      </Button>
    </div>
  );
}
