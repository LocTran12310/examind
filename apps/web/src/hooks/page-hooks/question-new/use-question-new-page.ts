import { useRouter } from "next/navigation";
import { useMemo } from "react";
import { formValueOf, payloadOf, type QuestionFormValue } from "@/components/common/QuestionForm/QuestionForm";
import { useCreateQuestionMutation } from "@/hooks/react-query/use-query-question";
import { useTagOptionsQuery } from "@/hooks/react-query/use-query-tag";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { useTopicsQuery } from "@/hooks/react-query/use-query-topic";
import { listHref } from "@/lib/common/list-memory";

/** A new question written by hand (Toán by default); saved → its page. */
export function useQuestionNewPage() {
  const router = useRouter();
  const { data: taxonomy } = useTaxonomyQuery();
  const { data: topics } = useTopicsQuery(null);
  const { data: tags } = useTagOptionsQuery(null);
  const create = useCreateQuestionMutation();
  const initial = useMemo(
    () => (taxonomy ? { ...formValueOf(), subject_id: taxonomy.subjects.find((s) => s.code === "toan")?.id ?? null } : null),
    [taxonomy],
  );
  return {
    taxonomy,
    topics,
    tags,
    initial,
    cancel: () => router.push(listHref("/org/bank")),
    save: async (v: QuestionFormValue) => {
      const q = await create.mutateAsync(payloadOf(v));
      router.push(`/org/bank/${q.id}`);
    },
  };
}
