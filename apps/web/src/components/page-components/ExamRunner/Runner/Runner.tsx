"use client";

import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { AnswerInput } from "@/components/common/AnswerInput/AnswerInput";
import { QuestionView } from "@/components/common/QuestionView/QuestionView";
import { Button } from "@/components/ui/button";
import { useExamRunner } from "@/hooks/page-hooks/exam-runner/use-exam-runner";
import type { AttemptView } from "@/interfaces/attempt.interface";
import { answered } from "@/lib/common/answer";
import { formatLeft } from "@/lib/page-libs/exam-runner/format-left";
import { cn } from "@/lib/utils";

/** The exam screen: one question at a time, the navigator, the countdown and "Nộp bài". */
export function Runner({ view, onFinished }: { view: AttemptView; onFinished: () => void }) {
  const r = useExamRunner(view, onFinished);
  const q = r.q;
  // `w-full` is load-bearing (AC-01): on a flex item `margin-inline: auto` cancels `align-items: stretch`, so
  // without it the frame shrinks to the width of whatever question is on screen and the page jumps on every move.
  return (
    <div className="mx-auto w-full max-w-5xl">
      <div className="sticky top-0 z-10 -mx-4 mb-4 flex flex-wrap items-center gap-3 border-b border-border bg-card/95 px-4 py-2 backdrop-blur">
        <span className="min-w-0 flex-1 truncate font-medium">{view.title}</span>
        <span className={cn("font-mono text-lg", r.left < 60_000 ? "text-destructive" : "text-foreground")} data-testid="timer">
          {formatLeft(r.left)}
        </span>
        {r.unsaved > 0 ? <ToneBadge tone="amber">Chưa lưu {r.unsaved}</ToneBadge> : <ToneBadge tone="green">Đã lưu</ToneBadge>}
        <Button onClick={() => r.setConfirming(true)} disabled={r.closed}>
          Nộp bài
        </Button>
      </div>
      {r.error && (
        <div className="mb-3">
          <FormAlert>{r.error}</FormAlert>
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-[1fr_220px]">
        <section className="rounded-xl border border-border bg-card p-4 sm:p-6" data-testid="exam-question">
          <div className="mb-2 text-xs text-muted-foreground">
            Phần {q.section} · {q.points} điểm
          </div>
          <QuestionView
            question={q}
            mode="exam"
            number={q.number}
            selected={r.selected}
            onSelect={q.type === "mcq" && !r.closed ? (label) => r.change({ key: label }) : undefined}
          />
          <AnswerInput q={q} value={r.answers[q.id]} onChange={r.change} />
          <div className="mt-6 flex justify-between">
            <Button variant="outline" disabled={r.index === 0} onClick={() => r.setIndex(r.index - 1)}>
              ← Câu trước
            </Button>
            <Button variant="outline" disabled={r.index === view.questions.length - 1} onClick={() => r.setIndex(r.index + 1)}>
              Câu sau →
            </Button>
          </div>
        </section>
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
                onClick={() => r.setIndex(i)}
                className={cn("px-0", i === r.index && "ring-2 ring-ring")}
              >
                {x.number}
              </Button>
            ))}
          </div>
        </aside>
      </div>
      <FormDialog open={r.confirming} title="Nộp bài?" onOpenChange={(o) => !o && r.setConfirming(false)}>
        <p className="mb-4 text-sm">
          {r.unanswered ? `Bạn còn ${r.unanswered} câu chưa làm. ` : ""}Sau khi nộp sẽ không sửa được nữa.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => r.setConfirming(false)}>
            Làm tiếp
          </Button>
          <Button onClick={() => void r.submitNow()}>Nộp bài</Button>
        </div>
      </FormDialog>
    </div>
  );
}
