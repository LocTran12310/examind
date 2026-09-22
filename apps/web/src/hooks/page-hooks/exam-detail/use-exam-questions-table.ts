import { useMemo } from "react";

/** The exam of the questions table, sent as a resource parameter of the search (not shown in the URL). */
export function useExamQuestionsTable(examId: string) {
  const params = useMemo(() => ({ exam_id: examId }), [examId]);
  return { params };
}
