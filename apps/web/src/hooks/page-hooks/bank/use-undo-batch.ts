import { useCallback, useMemo } from "react";
import { toast } from "sonner";
import { useUndoBatchMutation } from "@/hooks/react-query/use-query-question";
import { ApiError } from "@/lib/common/http";

/** "Hoàn tác" wherever the bank offers it: the toast of a bulk edit (AC-01) and each row of
 *  "Thay đổi gần đây" (AC-03). A refusal — too late, already taken back, a question since deleted — is the
 *  answer to a question the teacher asked, not a crash, so it is shown in the words the API already chose. */
export function useUndoBatch() {
  const { mutateAsync, isPending, variables } = useUndoBatchMutation();

  const run = useCallback(
    async (batchId: string) => {
      try {
        const { restored } = await mutateAsync(batchId);
        toast.success(`Đã hoàn tác ${restored} câu`);
      } catch (e) {
        toast.error(e instanceof ApiError ? e.message : "Không hoàn tác được");
      }
    },
    [mutateAsync],
  );

  // which batch is being restored, so a list of rows can disable itself while one of them is in flight
  return useMemo(() => ({ run, undoing: isPending ? (variables ?? null) : null }), [run, isPending, variables]);
}
