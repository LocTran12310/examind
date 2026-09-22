import { useState } from "react";
import { useAssignClassReviewMutation } from "@/hooks/react-query/use-query-practice";
import { fromLocalInput, toLocalInput } from "@/lib/common/dates";
import { formErrors } from "@/lib/common/form-errors";

const DAYS_OPEN = 3 * 86400_000;

/** "Giao đề ôn cá nhân": questions per exam, time limit and window (business time in the pickers, UTC on the wire). */
export function useClassAdaptiveDialog(classId: string, onDone: (created: number) => void) {
  const [v, setV] = useState({ count: 15, duration_minutes: 30, open_at: toLocalInput(new Date()), close_at: toLocalInput(new Date(Date.now() + DAYS_OPEN)) });
  const assign = useAssignClassReviewMutation(classId);
  const { fields, message } = formErrors(assign.error);
  return {
    v,
    setV,
    fields,
    message,
    busy: assign.isPending,
    submit: () =>
      assign.mutate({ ...v, open_at: fromLocalInput(v.open_at), close_at: fromLocalInput(v.close_at) }, { onSuccess: (r) => onDone(r.created) }),
  };
}
