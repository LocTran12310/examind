"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { AttemptQuestion } from "@/interfaces/attempt.interface";
import type { AnswerResponse as Resp } from "@/types/attempt.type";

/** Inputs for the parts QuestionView does not collect (true/false verdicts, short answers, essays). */
export function AnswerInput({ q, value, onChange }: { q: AttemptQuestion; value: Resp; onChange: (v: Resp) => void }) {
  if (q.type === "true_false") {
    const cur = (value ?? {}) as Record<string, boolean>;
    return (
      <div className="mt-3 space-y-2" data-testid="tf-input">
        {q.options.map((o) => (
          <div key={o.label} className="flex items-center gap-2 text-sm">
            <span className="w-6 font-semibold">{o.label})</span>
            {[true, false].map((v) => (
              <Button
                key={String(v)}
                type="button"
                variant="outline"
                aria-pressed={cur[o.label] === v}
                aria-label={`${o.label} ${v ? "Đúng" : "Sai"}`}
                onClick={() => onChange({ ...cur, [o.label]: v })}
                className={cn(
                  "px-3 font-normal",
                  cur[o.label] === v &&
                    (v
                      ? "border-emerald-600 bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/20 hover:text-emerald-700 dark:border-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400"
                      : "border-destructive bg-destructive/10 text-destructive hover:bg-destructive/20 hover:text-destructive dark:border-destructive dark:bg-destructive/10"),
                )}
              >
                {v ? "Đúng" : "Sai"}
              </Button>
            ))}
          </div>
        ))}
      </div>
    );
  }
  if (q.type === "short_answer") {
    return (
      <Input
        className="mt-3 max-w-xs"
        aria-label="Đáp án"
        placeholder="Nhập đáp án (ví dụ 2,5)"
        value={((value ?? {}) as { value?: string }).value ?? ""}
        onChange={(e) => onChange({ value: e.target.value })}
      />
    );
  }
  if (q.type === "essay") {
    return (
      <Textarea
        className="mt-3"
        rows={8}
        aria-label="Bài làm"
        placeholder="Trình bày lời giải…"
        value={((value ?? {}) as { text?: string }).text ?? ""}
        onChange={(e) => onChange({ text: e.target.value })}
      />
    );
  }
  return null;
}
