"use client";

import { useState } from "react";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useExamRunner } from "@/hooks/page-hooks/exam-runner/use-exam-runner";
import type { RunnerPaper } from "@/interfaces/attempt.interface";
import { answered } from "@/lib/common/answer";
import { cardId } from "@/lib/page-libs/exam-runner/card-id";
import { formatLeft } from "@/lib/page-libs/exam-runner/format-left";
import { cn } from "@/lib/utils";
import type { AnswerResponse } from "@/types/attempt.type";
import { PaperView } from "../PaperView/PaperView";
import { QuestionCard } from "../QuestionCard/QuestionCard";

/** Which questions the student is looking at; a page reload comes back to "one" on purpose (ADR-03). */
type ViewMode = "one" | "paper";

/**
 * The exam screen: one question or the whole paper, the navigator, the countdown and "Nộp bài".
 *
 * `trial` is the same screen sat by whoever set the exam (AC-04): there is no attempt behind it, so the countdown
 * and the saved badge have nothing to show and a badge saying so takes their place. The rest is deliberately one
 * screen and not two — a teacher who checks a paper must see exactly what the class will see.
 */
export function Runner({ view, trial, onFinished }: { view: RunnerPaper; trial?: boolean; onFinished: (answers: Record<string, AnswerResponse>) => void }) {
  const r = useExamRunner(view, onFinished, trial);
  const [mode, setMode] = useState<ViewMode>("one");
  const q = r.q;
  /** The navigator moves the current question in both modes; on the whole paper it also brings the card up. */
  const goTo = (i: number) => {
    r.setIndex(i);
    if (mode === "paper") document.getElementById(cardId(view.questions[i].id))?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  // `w-full` is load-bearing (AC-01): on a flex item `margin-inline: auto` cancels `align-items: stretch`, so
  // without it the frame shrinks to the width of whatever question is on screen and the page jumps on every move.
  return (
    <div className="mx-auto w-full max-w-5xl">
      <div className="sticky top-0 z-10 -mx-4 mb-4 flex flex-wrap items-center gap-3 border-b border-border bg-card/95 px-4 py-2 backdrop-blur">
        <span className="min-w-0 flex-1 truncate font-medium">{view.title}</span>
        <ToggleGroup type="single" variant="outline" size="sm" spacing={0} value={mode} aria-label="Chế độ xem" onValueChange={(v) => v && setMode(v as ViewMode)}>
          <ToggleGroupItem value="one">Một câu</ToggleGroupItem>
          <ToggleGroupItem value="paper">Toàn đề</ToggleGroupItem>
        </ToggleGroup>
        {r.left !== null && (
          <span className={cn("font-mono text-lg", r.left < 60_000 ? "text-destructive" : "text-foreground")} data-testid="timer">
            {formatLeft(r.left)}
          </span>
        )}
        {trial ? (
          <ToneBadge tone="amber">Chạy thử · không ghi lại gì</ToneBadge>
        ) : r.unsaved > 0 ? (
          <ToneBadge tone="amber">Chưa lưu {r.unsaved}</ToneBadge>
        ) : (
          <ToneBadge tone="green">Đã lưu</ToneBadge>
        )}
        <Button onClick={() => r.setConfirming(true)} disabled={r.closed}>
          {trial ? "Chấm thử" : "Nộp bài"}
        </Button>
      </div>
      {r.error && (
        <div className="mb-3">
          <FormAlert>{r.error}</FormAlert>
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-[1fr_220px]">
        {mode === "one" ? (
          <QuestionCard q={q} value={r.answers[q.id]} selected={r.selected} closed={r.closed} onChange={r.change}>
            <div className="mt-6 flex justify-between">
              <Button variant="outline" disabled={r.index === 0} onClick={() => r.setIndex(r.index - 1)}>
                ← Câu trước
              </Button>
              <Button variant="outline" disabled={r.index === view.questions.length - 1} onClick={() => r.setIndex(r.index + 1)}>
                Câu sau →
              </Button>
            </div>
          </QuestionCard>
        ) : (
          <PaperView questions={view.questions} answers={r.answers} keyOf={r.keyOf} closed={r.closed} onChange={r.change} />
        )}
        <aside className="rounded-xl border border-border bg-card p-3">
          <div className="mb-2 text-xs text-muted-foreground">Bảng câu · còn {r.unanswered} câu chưa làm</div>
          <div className="grid grid-cols-6 gap-1 md:grid-cols-5" data-testid="navigator">
            {view.questions.map((x, i) => (
              <Button
                key={x.id}
                type="button"
                size="sm"
                variant={answered(x, r.answers[x.id]) ? "default" : "outline"}
                aria-label={`Câu ${x.number}`}
                aria-current={i === r.index ? "true" : undefined}
                onClick={() => goTo(i)}
                className={cn("px-0", i === r.index && "ring-2 ring-ring")}
              >
                {x.number}
              </Button>
            ))}
          </div>
        </aside>
      </div>
      <FormDialog open={r.confirming} title={trial ? "Chấm bản chạy thử?" : "Nộp bài?"} onOpenChange={(o) => !o && r.setConfirming(false)}>
        <p className="mb-4 text-sm">
          {r.unanswered ? `Bạn còn ${r.unanswered} câu chưa làm. ` : ""}
          {trial ? "Bản chạy thử được chấm ngay và không ghi lại gì." : "Sau khi nộp sẽ không sửa được nữa."}
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => r.setConfirming(false)}>
            Làm tiếp
          </Button>
          <Button onClick={() => void r.submitNow()}>{trial ? "Chấm thử" : "Nộp bài"}</Button>
        </div>
      </FormDialog>
    </div>
  );
}
