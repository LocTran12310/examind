import { useRouter } from "next/navigation";
import { useMe } from "@/hooks/common/use-me";
import { useMyAssignmentsQuery, useStartAssignmentMutation } from "@/hooks/react-query/use-query-assignment";
import { ApiError } from "@/lib/common/http";

/** The student's home: open (still attemptable or in progress), upcoming and done assignments; start or resume one. */
export function useStudentHome() {
  const router = useRouter();
  const { data } = useMyAssignmentsQuery();
  const start = useStartAssignmentMutation();
  const all = data ?? [];
  return {
    loaded: !!data,
    open: all.filter((x) => x.state === "open" && (x.attempts_left > 0 || x.attempts.some((a) => a.status === "in_progress"))),
    upcoming: all.filter((x) => x.state === "upcoming"),
    done: all.filter((x) => x.attempts.some((a) => a.status === "submitted")),
    error: start.error ? (start.error instanceof ApiError ? start.error.message : "Không bắt đầu được") : null,
    start: (id: string) => start.mutate(id, { onSuccess: (r) => router.push(`/exam/${r.attempt_id}`) }),
  };
}

/** Greeting of the home page. */
export function useStudentHomePage() {
  const me = useMe();
  return { title: `Xin chào, ${me.full_name}`, orgName: me.org.name };
}
