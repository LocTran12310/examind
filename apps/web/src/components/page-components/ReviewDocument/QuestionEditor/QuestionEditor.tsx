"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { QuestionFields } from "@/components/common/QuestionFields/QuestionFields";
import { QuestionView } from "@/components/common/QuestionView/QuestionView";
import { Button } from "@/components/ui/button";
import { Kbd } from "@/components/ui/kbd";
import { useQuestionEditor } from "@/hooks/page-hooks/review-document/use-question-editor";
import type { ParsedQuestion, Question } from "@/interfaces/question.interface";

export function QuestionEditor({ question, onSaved, onCancel }: { question: ParsedQuestion; onSaved: (q: ParsedQuestion) => void; onCancel: () => void }) {
  const e = useQuestionEditor(question, onSaved);
  return (
    <div
      className="grid gap-4 lg:grid-cols-2"
      data-testid="editor"
      onKeyDown={(ev) => {
        if (ev.key === "Escape") onCancel();
      }}
    >
      <div>
        <QuestionFields draft={e.draft} setDraft={e.setDraft} />
        {e.error && <div className="mt-2"><FormAlert>{e.error}</FormAlert></div>}
        <div className="mt-3 flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>Hủy (Esc)</Button>
          <Button onClick={() => void e.save()} disabled={e.busy}>
            Lưu <Kbd className="ml-1 h-4 bg-primary-foreground/20 text-[10px] text-current">{e.hint}</Kbd>
          </Button>
        </div>
      </div>
      <div className="rounded-lg border border-dashed border-input p-3" data-testid="preview">
        <QuestionView question={{ ...question, ...e.draft } as Question} mode="review" solutionOpen />
      </div>
    </div>
  );
}
