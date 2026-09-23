import { useMe } from "@/hooks/common/use-me";
import { useAttemptQuery, useAttemptResultQuery } from "@/hooks/react-query/use-query-attempt";
import { ApiError } from "@/lib/common/http";

/** `/results/{id}`: the result (as the policy allows); staff also see whose attempt it is and grade essays. */
export function useAttemptResultPage(id: string) {
  const me = useMe();
  const staff = me.role === "org_admin" || me.role === "teacher";
  const result = useAttemptResultQuery(id);
  const { data: attempt } = useAttemptQuery(id, staff);
  return {
    result: result.data,
    error: result.error ? (result.error instanceof ApiError ? result.error.message : "Không tải được dữ liệu") : null,
    staff,
    description: staff && attempt ? `Bài làm của ${attempt.student.full_name} (${attempt.student.username})` : undefined,
    /** where the list this attempt sits in is: the report for staff, the student's own assignments otherwise */
    back: staff
      ? attempt?.assignment_id
        ? { href: `/org/assignments/${attempt.assignment_id}`, label: "Báo cáo bài giao" }
        : { href: "/org/exams", label: "Đề thi" }
      : { href: "/home", label: "Bài được giao" },
  };
}
