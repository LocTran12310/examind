import { useRouter } from "next/navigation";
import { useCallback, useEffect } from "react";
import { useAttemptQuery } from "@/hooks/react-query/use-query-attempt";
import { ApiError } from "@/lib/common/http";

/** `/exam/{id}`: the attempt while it is in progress; a submitted one goes to its result. */
export function useExamRunnerPage(id: string) {
  const router = useRouter();
  const { data, error } = useAttemptQuery(id);
  const toResult = useCallback(() => router.replace(`/results/${id}`), [router, id]);
  useEffect(() => {
    if (data && data.status !== "in_progress") toResult();
  }, [data, toResult]);
  return {
    view: data && data.status === "in_progress" ? data : null,
    error: error ? (error instanceof ApiError ? error.message : "Không tải được dữ liệu") : null,
    finished: toResult,
  };
}
