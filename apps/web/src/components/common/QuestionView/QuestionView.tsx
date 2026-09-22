"use client";

import { cn } from "@/lib/utils";
import { useState } from "react";
import type { Question } from "@/interfaces/question.interface";
import { Button } from "@/components/ui/button";
import { Markdown } from "@/components/common/Markdown/Markdown";

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
                <Button
                  type="button"
                  variant="outline"
                  disabled={!onSelect}
                  onClick={() => onSelect?.(o.label)}
                  data-testid={`option-${o.label}`}
                  data-correct={isKey || undefined}
                  className={cn(
                    // rich Markdown content: undo the button's single-line, centred, dimmed-when-disabled defaults
                    "h-auto w-full items-start justify-start gap-2 px-3 py-2 text-left font-normal whitespace-normal select-text hover:text-foreground disabled:opacity-100",
                    onSelect ? "cursor-pointer hover:border-primary dark:hover:border-primary" : "cursor-default",
                    isKey && "border-emerald-500 bg-emerald-500/10 dark:border-emerald-500 hover:bg-emerald-500/10 dark:bg-emerald-500/10 dark:hover:bg-emerald-500/10",
                    !isKey && isPicked && mode === "result" && "border-destructive bg-destructive/10 dark:border-destructive hover:bg-destructive/10 dark:bg-destructive/10 dark:hover:bg-destructive/10",
                    !isKey && isPicked && mode !== "result" && "border-primary bg-primary/10 dark:border-primary hover:bg-primary/10 dark:bg-primary/10 dark:hover:bg-primary/10",
                    !isKey && !isPicked && "border-border bg-transparent hover:bg-transparent dark:border-border dark:bg-transparent dark:hover:bg-transparent",
                  )}
                >
                  <span className="font-semibold">{o.label}.</span>
                  <div className="min-w-0 flex-1">
                    <Markdown>{o.content}</Markdown>
                  </div>
                  {reveal && q.type === "true_false" && o.is_true !== undefined && (
                    <span className={cn("text-sm font-medium", o.is_true ? "text-emerald-700 dark:text-emerald-400" : "text-destructive")}>{o.is_true ? "Đúng" : "Sai"}</span>
                  )}
                </Button>
              </li>
            );
          })}
        </ol>
      )}

      {reveal && q.answer && <AnswerBlock question={q} />}

      {reveal && q.solution?.trim() && (
        <section className="rounded-lg border border-border bg-muted/50" data-testid="solution">
          <Button type="button" variant="ghost" className="h-auto w-full justify-start rounded-lg px-3 py-2 text-left" onClick={() => setSolutionOpen((v) => !v)}>
            {solutionOpen ? "▾" : "▸"} Lời giải
          </Button>
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
