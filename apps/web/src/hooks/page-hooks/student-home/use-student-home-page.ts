import { useRouter } from "next/navigation";
import { useMe } from "@/hooks/common/use-me";
import { useMyAssignmentsQuery, useStartAssignmentMutation } from "@/hooks/react-query/use-query-assignment";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { ApiError } from "@/lib/common/http";
import { groupBySubject } from "@/lib/page-libs/student-home/group-by-subject";

/** The student's home: open (still attemptable or in progress), upcoming and done assignments; start or resume one. */
export function useStudentHome() {
  const router = useRouter();
  const { data } = useMyAssignmentsQuery();
  const start = useStartAssignmentMutation();
  const { data: taxonomy } = useTaxonomyQuery();
  const names = new Map((taxonomy?.subjects ?? []).map((s) => [s.id, s.name]));
  const all = data ?? [];
  return {
    loaded: !!data,
    /** each section splits under its subjects, and stays one flat list while they are all the same */
    groups: <T extends { subject_id?: string | null }>(rows: T[]) => groupBySubject(rows, names),
    open: all.filter((x) => x.state === "open" && (x.attempts_left > 0 || x.attempts.some((a) => a.status === "in_progress"))),
    upcoming: all.filter((x) => x.state === "upcoming"),
    done: all.filter((x) => x.attempts.some((a) => a.status === "submitted")),
    error: start.error ? (start.error instanceof ApiError ? start.error.message : "Không bắt đầu được") : null,
    start: (id: string) => start.mutate(id, { onSuccess: (r) => router.push(`/exam/${r.attempt_id}`) }),
  };
}

/** Greeting of the home page. `canPractise` is the one thing that does not nest with the roles: a practice run
 *  writes a real attempt and real answer facts, so a teacher's would land in the organisation's numbers as if a
 *  student had sat it. Staff reach this page and see their own assignments — usually none. */
export function useStudentHomePage() {
  const me = useMe();
  return { title: `Xin chào, ${me.full_name}`, orgName: me.org.name, canPractise: me.role === "student" };
}
