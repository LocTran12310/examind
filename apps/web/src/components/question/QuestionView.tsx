"use client";

import { cn } from "@/lib/utils";
import { useState } from "react";
import type { Question } from "@/lib/types";
import { Markdown } from "./Markdown";

export type QuestionMode = "exam" | "review" | "result";

const DIFFICULTY: Record<string, string> = { nb: "Nhận biết", th: "Thông hiểu", vd: "Vận dụng", vdc: "Vận dụng cao" };

/**
 * The only question renderer (architecture map): stem, options, answer and solution with KaTeX and images.
 * - exam: answer + solution hidden, options selectable
 * - review: everything visible, correct option highlighted
 * - result: like review, plus the student's choice marked right/wrong
 */
export function QuestionView({
  question: q,
  mode = "review",
  number,
  selected,
  onSelect,
  solutionOpen: solutionOpenProp,
}: {
  question: Question;
  mode?: QuestionMode;
  number?: number;
  selected?: string | null;
  onSelect?: (label: string) => void;
  solutionOpen?: boolean;
}) {
  const [solutionOpen, setSolutionOpen] = useState(solutionOpenProp ?? mode === "review");
  const reveal = mode !== "exam";
  const key = q.answer?.key;

  return (
    <article className="space-y-3" data-testid="question">
      <header className="flex items-baseline gap-2">
        {number !== undefined && <span className="font-semibold">Câu {number}.</span>}
        {reveal && q.difficulty && <span className="text-xs text-muted-foreground">{DIFFICULTY[q.difficulty] ?? q.difficulty}</span>}
      </header>
      <Markdown>{q.stem}</Markdown>

      {q.options.length > 0 && (
        <ol className="grid gap-2" data-testid="options">
          {q.options.map((o) => {
            const isKey = reveal && q.type === "mcq" && key === o.label;
            const isPicked = selected === o.label;
            return (
              <li key={o.label}>
                <button
                  type="button"
                  disabled={!onSelect}
                  onClick={() => onSelect?.(o.label)}
                  data-testid={`option-${o.label}`}
                  data-correct={isKey || undefined}
                  className={cn(
                    "flex w-full items-start gap-2 rounded-lg border px-3 py-2 text-left",
                    onSelect ? "cursor-pointer hover:border-primary" : "cursor-default",
                    isKey && "border-green-500 bg-emerald-500/10",
                    !isKey && isPicked && mode === "result" && "border-destructive bg-destructive/10",
                    !isKey && isPicked && mode !== "result" && "border-primary bg-primary/10",
                    !isKey && !isPicked && "border-border",
                  )}
                >
                  <span className="font-semibold">{o.label}.</span>
                  <div className="min-w-0 flex-1">
                    <Markdown>{o.content}</Markdown>
                  </div>
                  {reveal && q.type === "true_false" && o.is_true !== undefined && (
                    <span className={cn("text-sm font-medium", o.is_true ? "text-emerald-700 dark:text-emerald-400" : "text-destructive")}>{o.is_true ? "Đúng" : "Sai"}</span>
                  )}
                </button>
              </li>
            );
          })}
        </ol>
      )}

      {reveal && q.answer && <AnswerBlock question={q} />}

      {reveal && q.solution?.trim() && (
        <section className="rounded-lg border border-border bg-muted/50" data-testid="solution">
          <button type="button" className="w-full px-3 py-2 text-left text-sm font-medium" onClick={() => setSolutionOpen((v) => !v)}>
            {solutionOpen ? "▾" : "▸"} Lời giải
          </button>
          {solutionOpen && (
            <div className="border-t border-border px-3 py-2">
              <Markdown>{q.solution}</Markdown>
            </div>
          )}
        </section>
      )}
    </article>
  );
}

function AnswerBlock({ question: q }: { question: Question }) {
  const a = q.answer ?? {};
  let text: string | null = null;
  if (q.type === "mcq" && a.key) text = `Đáp án: ${a.key}`;
  if (q.type === "short_answer" && a.value) text = `Đáp án: ${a.value}`;
  if (q.type === "true_false")
    text = "Đáp án: " + q.options.map((o) => `${o.label}) ${o.is_true ? "Đ" : "S"}`).join("  ");
  if (q.type === "essay" && a.text)
    return (
      <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm" data-testid="answer">
        <div className="font-medium">Đáp án mẫu</div>
        <Markdown>{a.text}</Markdown>
      </div>
    );
  if (!text) return null;
  return (
    <div className="text-sm font-medium text-emerald-700 dark:text-emerald-400" data-testid="answer">
      {text}
    </div>
  );
}
