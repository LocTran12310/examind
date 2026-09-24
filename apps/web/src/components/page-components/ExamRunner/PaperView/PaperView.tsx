"use client";

import type { AttemptQuestion } from "@/interfaces/attempt.interface";
import { cardId } from "@/lib/page-libs/exam-runner/card-id";
import type { AnswerResponse } from "@/types/attempt.type";
import { QuestionCard } from "../QuestionCard/QuestionCard";

/**
 * The whole paper down the page, every question with its own input (AC-02, AC-03): what a student does with a
 * paper exam — read it all, then answer the easy ones first. Same cards, same `change()`, so autosave, the
 * navigator and the unanswered count behave exactly as in one-question mode.
 */
export function PaperView({
  questions,
  answers,
  keyOf,
  closed,
  onChange,
}: {
  questions: AttemptQuestion[];
  answers: Record<string, AnswerResponse>;
  keyOf: (q: AttemptQuestion) => string | null;
  closed: boolean;
  onChange: (v: AnswerResponse, questionId: string) => void;
}) {
  return (
    <div className="space-y-4" data-testid="exam-paper">
      {questions.map((q) => (
        <QuestionCard key={q.id} id={cardId(q.id)} q={q} value={answers[q.id]} selected={keyOf(q)} closed={closed} onChange={(v) => onChange(v, q.id)} />
      ))}
    </div>
  );
}
