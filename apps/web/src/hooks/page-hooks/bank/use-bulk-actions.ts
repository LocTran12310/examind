import { useState } from "react";
import { toast } from "sonner";
import { useUndoBatch } from "@/hooks/page-hooks/bank/use-undo-batch";
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
  const undo = useUndoBatch();

  async function apply(set: Record<string, unknown>, label: string) {
    try {
      const r = await bulk.mutateAsync({ ids, set });
      // the toast is the only moment the teacher still remembers what was selected, so the way back rides on it
      // (AC-01); an edit found later goes back through "Thay đổi gần đây", which reads the same batches.
      toast.success(`${label}: ${r.updated} câu`, { action: { label: "Hoàn tác", onClick: () => void undo.run(r.batch_id) } });
      // the selection is what is *being worked on*, and after the edit it no longer is: a subject change moves
      // those questions out of the tab they were picked in, so the toolbar went on saying "Đã chọn 21" over an
      // empty list. Undo does not need it — it rides on the batch id in the toast, not on what is ticked.
      onClear();
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
