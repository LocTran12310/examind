import { useState } from "react";
import { useCreateAssignmentMutation } from "@/hooks/react-query/use-query-assignment";
import type { Assignment } from "@/interfaces/assignment.interface";
import { formErrors } from "@/lib/common/form-errors";
import { fromBusinessInput, toBusinessInput } from "@/lib/datetime";
import type { ResultsPolicy } from "@/types/assignment.type";

const WEEK = 7 * 86400_000;

/** "Giao bài": title, classes, window (business time in the pickers, UTC on the wire) and policies. */
export function useAssignDialog(examId: string, title: string, onDone: (a: Assignment) => void) {
  const [v, setV] = useState({
    title,
    open_at: toBusinessInput(new Date()),
    close_at: toBusinessInput(new Date(Date.now() + WEEK)),
    duration_minutes: 45,
    max_attempts: 1,
    shuffle_questions: true,
    shuffle_options: true,
    results_policy: "after_submit" as ResultsPolicy,
    class_ids: [] as string[],
  });
  const create = useCreateAssignmentMutation();
  const { fields, message } = formErrors(create.error);
  const set = <K extends keyof typeof v>(k: K, val: (typeof v)[K]) => setV((x) => ({ ...x, [k]: val }));
  return {
    v,
    set,
    fields,
    message,
    busy: create.isPending,
    toggleClass: (id: string, on: boolean) => set("class_ids", on ? [...v.class_ids, id] : v.class_ids.filter((x) => x !== id)),
    submit: () =>
      create.mutate({ ...v, exam_id: examId, open_at: fromBusinessInput(v.open_at), close_at: fromBusinessInput(v.close_at) }, { onSuccess: (a) => onDone(a) }),
  };
}
