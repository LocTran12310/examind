import { useState } from "react";
import { toast } from "sonner";
import { useBulkUpdateQuestionsMutation, useDeleteQuestionsMutation } from "@/hooks/react-query/use-query-question";
import { ApiError } from "@/lib/common/http";

/** Bulk changes and delete of the selected questions (the lists refresh through the question keys). */
export function useBulkActions({ ids, onDone, onClear }: { ids: string[]; onDone?: () => void; onClear: () => void }) {
  const [picking, setPicking] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const bulk = useBulkUpdateQuestionsMutation();
  const removeMany = useDeleteQuestionsMutation();

  async function apply(set: Record<string, unknown>, label: string) {
    try {
      const r = await bulk.mutateAsync({ ids, set });
      toast.success(`${label}: ${r.updated} câu`);
      onDone?.();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  async function remove() {
    const { failed } = await removeMany.mutateAsync(ids);
    if (failed) toast.error(`${failed} câu không xóa được (đang dùng trong đề)`);
    else toast.success(`Đã xóa ${ids.length} câu`);
    onClear();
    onDone?.();
  }

  return { none: ids.length === 0, picking, setPicking, confirming, setConfirming, apply, remove };
}
