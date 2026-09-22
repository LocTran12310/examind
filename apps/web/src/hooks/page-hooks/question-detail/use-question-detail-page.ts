import { useState } from "react";
import type { QuestionFormValue } from "@/components/common/QuestionForm/QuestionForm";
import { payloadOf } from "@/components/common/QuestionForm/QuestionForm";
import { useQuestionQuery, useUpdateQuestionMutation } from "@/hooks/react-query/use-query-question";
import { useTagOptionsQuery } from "@/hooks/react-query/use-query-tag";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { useTopicsQuery } from "@/hooks/react-query/use-query-topic";

/** One question of the bank: read it, or edit it in the full form. */
export function useQuestionDetailPage(id: string) {
  const { data: question } = useQuestionQuery(id);
  const { data: taxonomy } = useTaxonomyQuery();
  // a question with a subject only offers that subject's topics and tags (subject-scoped-bank, ui-polish A-04)
  const sid = question?.subject_id ?? null;
  const { data: topics } = useTopicsQuery(sid, !!question);
  const { data: tags } = useTagOptionsQuery(sid, !!question);
  const update = useUpdateQuestionMutation();
  const [editing, setEditing] = useState(false);
  return {
    question,
    taxonomy,
    topics,
    tags,
    ready: !!(question && taxonomy && topics && tags),
    editing,
    setEditing,
    save: async (v: QuestionFormValue) => {
      await update.mutateAsync({ id, body: payloadOf(v) });
      setEditing(false);
    },
  };
}
