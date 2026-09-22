import { useRouter } from "next/navigation";
import { useStartPracticeMutation } from "@/hooks/react-query/use-query-practice";
import { ApiError } from "@/lib/common/http";

/** "Tạo đề ôn tập": a practice exam planned for the student, then straight into the runner. */
export function usePracticeButton(count: number) {
  const router = useRouter();
  const start = useStartPracticeMutation();
  // busy until the runner opens (the button stays disabled while the page changes)
  const busy = start.isPending || start.isSuccess;
  return {
    busy,
    error: start.error ? (start.error instanceof ApiError ? start.error.message : "Không tạo được đề") : null,
    start: () => start.mutate({ count }, { onSuccess: (r) => router.push(`/exam/${r.attempt_id}`) }),
  };
}
