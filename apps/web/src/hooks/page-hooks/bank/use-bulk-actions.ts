import { useState } from "react";
import { toast } from "sonner";
import { useBulkUpdateQuestionsMutation, useDeleteQuestionsMutation, useTopicCountsQuery } from "@/hooks/react-query/use-query-question";
import type { SubjectTopicConflict } from "@/interfaces/question.interface";
import { ApiError } from "@/lib/common/http";
import { subjectTopicConflicts } from "@/lib/page-libs/bank/conflicts";

/** What a refused subject change left on screen: the message and the questions in the way (A-04). */
export interface ConflictNotice {
  message: string;
  conflicts: SubjectTopicConflict[];
}

/** Bulk changes and delete of the selected questions (the lists refresh through the question keys). */
export function useBulkActions({ ids, subjectId, onDone, onClear }: { ids: string[]; subjectId?: string | null; onDone?: () => void; onClear: () => void }) {
  const [picking, setPicking] = useState(false);
  const [confirming, setConfirming] = useState(false);
  // a subject the topics contradict is refused whole; the teacher is shown which questions and what to do
  const [conflict, setConflict] = useState<ConflictNotice | null>(null);
  // the picker's numbers are questions of the subject in hand, asked for only when it opens (ADR-01)
  const { data: topicCounts } = useTopicCountsQuery(subjectId, picking);
  const bulk = useBulkUpdateQuestionsMutation();
  const removeMany = useDeleteQuestionsMutation();

  async function apply(set: Record<string, unknown>, label: string) {
    try {
      const r = await bulk.mutateAsync({ ids, set });
      toast.success(`${label}: ${r.updated} câu`);
      onDone?.();
    } catch (e) {
      const conflicts = subjectTopicConflicts(e);
      if (conflicts) setConflict({ message: (e as ApiError).message, conflicts });
      else toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  async function remove() {
    const { failed } = await removeMany.mutateAsync(ids);
    if (failed) toast.error(`${failed} câu không xóa được (đang dùng trong đề)`);
    else toast.success(`Đã xóa ${ids.length} câu`);
    onClear();
    onDone?.();
  }

  return { none: ids.length === 0, picking, setPicking, topicCounts, confirming, setConfirming, conflict, setConflict, apply, remove };
}
