import { useRouter } from "next/navigation";
import { useState } from "react";
import { useStartPracticeMutation } from "@/hooks/react-query/use-query-practice";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { ApiError } from "@/lib/common/http";

/** "Tạo đề ôn tập": a practice exam planned for the student, then straight into the runner.
 *
 *  The subject is asked for first when the centre teaches more than one (A-01), because the plan is drawn inside
 *  one subject and the exam records which (ADR-01). With a single subject there is nothing to ask — but it is
 *  still sent, so the exam carries a subject there too and the history can say what it was. */
export function usePracticeButton(count: number, defaultSubjectId?: string | null) {
  const router = useRouter();
  const start = useStartPracticeMutation();
  const { data: taxonomy } = useTaxonomyQuery();
  const subjects = taxonomy?.subjects ?? [];
  const [asking, setAsking] = useState(false);
  const [chosen, setChosen] = useState("");
  // busy until the runner opens (the button stays disabled while the page changes)
  const busy = start.isPending || start.isSuccess;

  const go = (subjectId?: string) =>
    start.mutate({ count, ...(subjectId ? { subject_id: subjectId } : {}) }, { onSuccess: (r) => router.push(`/exam/${r.attempt_id}`) });

  return {
    busy,
    subjects,
    asking,
    chosen,
    setChosen,
    close: () => setAsking(false),
    error: start.error ? (start.error instanceof ApiError ? start.error.message : "Không tạo được đề") : null,
    /** one subject: straight in. Several: ask, starting on the one the caller says is weakest (A-03) */
    start: () => {
      if (subjects.length > 1) {
        setChosen(defaultSubjectId || subjects[0].id);
        setAsking(true);
        return;
      }
      go(subjects[0]?.id);
    },
    confirm: () => {
      setAsking(false);
      go(chosen);
    },
  };
}
