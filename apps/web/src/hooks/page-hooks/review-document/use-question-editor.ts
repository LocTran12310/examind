import { useState } from "react";
import { draftOf, type Draft } from "@/components/common/QuestionFields/QuestionFields";
import { useUpdateQuestionMutation } from "@/hooks/react-query/use-query-question";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import { ApiError } from "@/lib/common/http";
import { useSaveHint, useSaveShortcut } from "@/lib/shortcuts";

/** Inline edit of a queued question: the draft, saving (also ⌘/Ctrl+Enter) and its error. */
export function useQuestionEditor(question: ParsedQuestion, onSaved: (q: ParsedQuestion) => void) {
  const [draft, setDraft] = useState<Draft>(draftOf(question));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const update = useUpdateQuestionMutation();
  useSaveShortcut(() => {
    if (!busy) void save();
  });
  const hint = useSaveHint();

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const body = { type: draft.type, stem: draft.stem, options: draft.options, answer: draft.answer ?? {}, solution: draft.solution };
      onSaved(await update.mutateAsync({ id: question.id, body }));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không lưu được");
    } finally {
      setBusy(false);
    }
  }

  return { draft, setDraft, error, busy, hint, save };
}
