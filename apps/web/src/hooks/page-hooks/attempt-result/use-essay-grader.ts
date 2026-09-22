import { useState } from "react";
import { useGradeAnswerMutation } from "@/hooks/react-query/use-query-attempt";
import { ApiError } from "@/lib/common/http";

/** Points and comment of one essay answer; saving refreshes the result and the assignment report. */
export function useEssayGrader(attemptId: string, questionId: string, points: number | null, comment: string | null) {
  const [p, setP] = useState(points === null ? "" : String(points));
  const [c, setC] = useState(comment ?? "");
  const grade = useGradeAnswerMutation(attemptId);
  return {
    points: p,
    setPoints: setP,
    comment: c,
    setComment: setC,
    error: grade.error ? (grade.error instanceof ApiError ? grade.error.message : "Không lưu được") : null,
    save: () => grade.mutate({ questionId, body: { points: Number(p), comment: c || null } }),
  };
}
