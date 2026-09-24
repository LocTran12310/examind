"use client";

import { AnswerInput } from "@/components/common/AnswerInput/AnswerInput";
import { QuestionView } from "@/components/common/QuestionView/QuestionView";
import type { AttemptQuestion } from "@/interfaces/attempt.interface";
import type { AnswerResponse } from "@/types/attempt.type";

/** One question the way the student answers it — the same card in both view modes, so the two cannot drift. */
export function QuestionCard({
  q,
  value,
  selected,
  closed,
  onChange,
  id,
  children,
}: {
  q: AttemptQuestion;
  value: AnswerResponse;
  selected: string | null;
  closed: boolean;
  onChange: (v: AnswerResponse) => void;
  id?: string;
  children?: React.ReactNode;
}) {
  return (
    <section id={id} className="rounded-xl border border-border bg-card p-4 sm:p-6" data-testid="exam-question">
      <div className="mb-2 text-xs text-muted-foreground">
        Phần {q.section} · {q.points} điểm
      </div>
      <QuestionView question={q} mode="exam" number={q.number} selected={selected} onSelect={q.type === "mcq" && !closed ? (label) => onChange({ key: label }) : undefined} />
      <AnswerInput q={q} value={value} onChange={onChange} />
      {children}
    </section>
  );
}
