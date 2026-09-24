import { useCallback } from "react";
import { useAssignmentPaperQuery, useTrialMutation } from "@/hooks/react-query/use-query-assignment";
import { ApiError } from "@/lib/common/http";
import type { AnswerResponse } from "@/types/attempt.type";

/** `/org/assignments/{id}/trial`: the paper is read once and the answers are graded in one call when the runner
 *  finishes. There is nothing in between — no attempt, no autosave — because a trial run writes nothing
 *  (exam-runner ADR-01), which is also why the grade only lives as long as this page does. */
export function useExamTrialPage(id: string) {
  const paper = useAssignmentPaperQuery(id);
  const { mutateAsync: grade, data: result, error: gradeError } = useTrialMutation(id);
  const graded = useCallback((answers: Record<string, AnswerResponse>) => void grade({ responses: answers }).catch(() => undefined), [grade]);
  return {
    paper: paper.data,
    result,
    error: paper.error
      ? paper.error instanceof ApiError
        ? paper.error.message
        : "Không tải được dữ liệu"
      : gradeError
        ? gradeError instanceof ApiError
          ? gradeError.message
          : "Không chấm được bản chạy thử"
        : null,
    graded,
    /** the exam this paper was given from — the page the trial was started on */
    back: paper.data ? `/org/exams/${paper.data.exam_id}` : "/org/exams",
  };
}
